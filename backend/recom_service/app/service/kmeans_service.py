import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Set
from collections import Counter
import json
import random

MAX_GLOBAL_TAG_FEATURES = 50


class KMeansRecommender:
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.scaler = StandardScaler()
        self.user_clusters = {}
        self.manga_features = {}

    @staticmethod
    def parse_tags_cell(tags_raw) -> List[str]:
        if tags_raw is None:
            return []
        if isinstance(tags_raw, list):
            return [str(t).strip() for t in tags_raw if str(t).strip()]
        if isinstance(tags_raw, str):
            s = tags_raw.strip()
            if not s:
                return []
            try:
                parsed = json.loads(s.replace("'", '"'))
                if isinstance(parsed, list):
                    return [str(t).strip() for t in parsed if str(t).strip()]
            except json.JSONDecodeError:
                pass
            return [t.strip() for t in s.split(",") if t.strip()]
        return []

    @staticmethod
    def _user_profile_tags_lower(user_id: int, db: Session) -> Set[str]:
        q = text(
            """
            SELECT m.tags FROM favorites f
            JOIN mangas m ON f.manga_id = m.id
            WHERE f.user_id = :user_id
            """
        )
        profile: Set[str] = set()
        for (tags_raw,) in db.execute(q, {"user_id": user_id}).fetchall():
            for t in KMeansRecommender.parse_tags_cell(tags_raw):
                profile.add(t.lower())
        return profile

    @staticmethod
    def tag_based_recommendations(user_id: int, db: Session, limit: int = 10) -> List[int]:
        """Content-based: rank mangas not yet favorited by tag overlap with user's favorites."""
        profile_tags = KMeansRecommender._user_profile_tags_lower(user_id, db)
        cand_q = text(
            """
            SELECT m.id, m.tags, m.rating
            FROM mangas m
            WHERE m.id NOT IN (SELECT manga_id FROM favorites WHERE user_id = :user_id)
            """
        )
        rows = db.execute(cand_q, {"user_id": user_id}).fetchall()
        scored = []
        for mid, tags_raw, rating in rows:
            mtags = {t.lower() for t in KMeansRecommender.parse_tags_cell(tags_raw)}
            overlap = len(profile_tags & mtags) if profile_tags else 0
            r = float(rating) if rating is not None else 0.0
            scored.append((overlap, r, random.random(), mid))
        scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
        return [x[3] for x in scored[:limit]]

    def _rerank_ids_by_profile_tags(
        self, user_id: int, manga_ids: List[int], db: Session, limit: int
    ) -> List[int]:
        if not manga_ids:
            return []
        profile_tags = self._user_profile_tags_lower(user_id, db)
        if not profile_tags:
            return manga_ids[:limit]
        uniq = list(dict.fromkeys(manga_ids))
        q = text("SELECT id, tags FROM mangas WHERE id IN :ids")
        rows = db.execute(q, {"ids": tuple(uniq)}).fetchall()
        scored = []
        for mid, tags_raw in rows:
            mtags = {t.lower() for t in self.parse_tags_cell(tags_raw)}
            ov = len(profile_tags & mtags)
            scored.append((ov, random.random(), mid))
        scored.sort(key=lambda x: (-x[0], x[1]))
        ordered = [mid for _, _, mid in scored]
        rest = [m for m in uniq if m not in ordered]
        return (ordered + rest)[:limit]

    def prepare_user_features(self, db: Session) -> pd.DataFrame:
        """Prepares user features based on their favorites.

        Tag dimensions are aligned globally: column g_tag_i is always the same tag
        (one of the most frequent tags in the favorites dataset) for every user.
        """
        query = text(
            """
            SELECT
                f.user_id,
                f.manga_id,
                m.rating,
                m.year,
                m.tags
            FROM favorites f
            JOIN mangas m ON f.manga_id = m.id
            """
        )

        result = db.execute(query)
        data = result.fetchall()

        if not data:
            print("No favorites found in database!")
            debug_query = text("SELECT COUNT(*) FROM favorites")
            fav_count = db.execute(debug_query).scalar()
            print(f"   Total favorites in table: {fav_count}")

            if fav_count > 0:
                debug_query2 = text(
                    """
                    SELECT COUNT(*)
                    FROM favorites f
                    LEFT JOIN mangas m ON f.manga_id = m.id
                    WHERE m.id IS NULL
                    """
                )
                orphan_favs = db.execute(debug_query2).scalar()
                if orphan_favs > 0:
                    print(f"   {orphan_favs} favorites without corresponding manga!")

            return pd.DataFrame()

        unique_users = len(set(row[0] for row in data))
        print(f"Found {len(data)} favorites from {unique_users} users")

        sample_users = list(set(row[0] for row in data))[:5]
        print(f"   Example user_ids: {sample_users}")

        df = pd.DataFrame(data, columns=["user_id", "manga_id", "rating", "year", "tags"])
        df["tags"] = df["tags"].apply(self.parse_tags_cell)

        freq = Counter()
        for tags_list in df["tags"]:
            if isinstance(tags_list, list):
                for t in tags_list:
                    freq[t.lower()] += 1

        top_tag_keys = [t for t, _ in freq.most_common(MAX_GLOBAL_TAG_FEATURES)]

        user_features = []

        for user_id in df["user_id"].unique():
            user_data = df[df["user_id"] == user_id]

            avg_rating = user_data["rating"].mean() if not user_data["rating"].isna().all() else 0
            avg_year = user_data["year"].mean() if not user_data["year"].isna().all() else 0
            num_favorites = len(user_data)

            uc = Counter()
            for tags_list in user_data["tags"]:
                if isinstance(tags_list, list):
                    for t in tags_list:
                        uc[t.lower()] += 1

            row = {
                "user_id": user_id,
                "avg_rating": avg_rating,
                "avg_year": avg_year,
                "num_favorites": num_favorites,
            }
            for i, tl in enumerate(top_tag_keys):
                row[f"g_tag_{i}"] = uc.get(tl, 0)

            user_features.append(row)

        return pd.DataFrame(user_features)

    def train(self, db: Session):
        """Trains the K-Means model with user data"""
        try:
            user_features = self.prepare_user_features(db)

            if user_features.empty:
                return False

            if len(user_features) < 2:
                return False

            actual_clusters = min(max(2, len(user_features) // 2), self.n_clusters)

            feature_cols = [col for col in user_features.columns if col != "user_id"]
            X = user_features[feature_cols].fillna(0)

            if X.std().sum() == 0:
                return False

            X_scaled = self.scaler.fit_transform(X)

            self.kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
            clusters = self.kmeans.fit_predict(X_scaled)

            self.user_clusters = dict(zip(user_features["user_id"], clusters))

            print(f"Model trained with {len(user_features)} users in {actual_clusters} clusters")
            return True
        except Exception as e:
            print(f"Error training K-Means: {e}")
            import traceback

            traceback.print_exc()
            return False

    def get_recommendations(self, user_id: int, db: Session, limit: int = 10) -> List[int]:
        """Returns manga recommendations for a user"""
        if not self.kmeans or user_id not in self.user_clusters:
            print(f"Model not trained or user {user_id} is not in the model")
            return []

        user_cluster = self.user_clusters[user_id]
        print(f"User {user_id} is in cluster {user_cluster}")

        similar_users = [
            uid for uid, cluster in self.user_clusters.items() if cluster == user_cluster and uid != user_id
        ]

        print(f"   Found {len(similar_users)} similar users in cluster {user_cluster}")

        if not similar_users:
            print(f"No similar users found in cluster {user_cluster}")
            print(f"   Trying to find users from other clusters...")

            all_other_users = [
                uid for uid, cluster in self.user_clusters.items() if cluster != user_cluster and uid != user_id
            ]

            if all_other_users:
                print(f"   Found {len(all_other_users)} users in other clusters")
                if len(all_other_users) == 1:
                    query = text(
                        """
                        SELECT DISTINCT f.manga_id
                        FROM favorites f
                        WHERE f.user_id = :similar_user
                        AND f.manga_id NOT IN (
                            SELECT manga_id FROM favorites WHERE user_id = :user_id
                        )
                        ORDER BY RAND()
                        LIMIT :limit
                        """
                    )
                    result = db.execute(
                        query,
                        {"similar_user": all_other_users[0], "user_id": user_id, "limit": limit},
                    )
                else:
                    selected_users = all_other_users[:10]
                    query = text(
                        """
                        SELECT DISTINCT f.manga_id, COUNT(*) as popularity
                        FROM favorites f
                        WHERE f.user_id IN :similar_users
                        AND f.manga_id NOT IN (
                            SELECT manga_id FROM favorites WHERE user_id = :user_id
                        )
                        GROUP BY f.manga_id
                        ORDER BY popularity DESC, RAND()
                        LIMIT :limit
                        """
                    )
                    result = db.execute(
                        query,
                        {"similar_users": tuple(selected_users), "user_id": user_id, "limit": limit},
                    )

                recommendations = [row[0] for row in result.fetchall()]
                recommendations = self._rerank_ids_by_profile_tags(user_id, recommendations, db, limit)
                print(f"   Found {len(recommendations)} recommendations from other clusters (reranked by tags)")

                if recommendations:
                    return recommendations

            print(f"   Using tag-based fallback (replacing global popularity)")
            return self.tag_based_recommendations(user_id, db, limit)

        user_favs_query = text("SELECT COUNT(*) FROM favorites WHERE user_id = :user_id")
        user_fav_count = db.execute(user_favs_query, {"user_id": user_id}).scalar()
        print(f"   User {user_id} has {user_fav_count} favorites")

        if len(similar_users) == 1:
            similar_favs_query = text("SELECT COUNT(*) FROM favorites WHERE user_id = :similar_user")
            similar_fav_count = db.execute(similar_favs_query, {"similar_user": similar_users[0]}).scalar()
        else:
            similar_favs_query = text("SELECT COUNT(*) FROM favorites WHERE user_id IN :similar_users")
            similar_fav_count = db.execute(
                similar_favs_query, {"similar_users": tuple(similar_users)}
            ).scalar()
        print(f"   Similar users have {similar_fav_count} favorites in total")

        if len(similar_users) == 1:
            user_favs_subquery = text("SELECT manga_id FROM favorites WHERE user_id = :user_id")
            user_favs = [row[0] for row in db.execute(user_favs_subquery, {"user_id": user_id}).fetchall()]

            similar_user_favs_query = text(
                "SELECT DISTINCT manga_id FROM favorites WHERE user_id = :similar_user"
            )
            similar_user_favs = [
                row[0]
                for row in db.execute(
                    similar_user_favs_query, {"similar_user": similar_users[0]}
                ).fetchall()
            ]

            available_mangas = [m for m in similar_user_favs if m not in user_favs]

            if len(available_mangas) >= limit:
                recommendations = random.sample(available_mangas, limit)
            elif len(available_mangas) > 0:
                recommendations = available_mangas
            else:
                recommendations = []

            recommendations = self._rerank_ids_by_profile_tags(user_id, recommendations, db, limit)

            print(
                f"   User {similar_users[0]} has {len(similar_user_favs)} favorites, "
                f"{len(available_mangas)} available for recommendation"
            )
            return recommendations
        else:
            query = text(
                """
                SELECT DISTINCT f.manga_id, COUNT(*) as popularity
                FROM favorites f
                WHERE f.user_id IN :similar_users
                AND f.manga_id NOT IN (
                    SELECT manga_id FROM favorites WHERE user_id = :user_id
                )
                GROUP BY f.manga_id
                ORDER BY popularity DESC, RAND()
                LIMIT :limit
                """
            )
            result = db.execute(
                query,
                {"similar_users": tuple(similar_users), "user_id": user_id, "limit": limit},
            )

        recommendations = [row[0] for row in result.fetchall()]
        recommendations = self._rerank_ids_by_profile_tags(user_id, recommendations, db, limit)

        unique_manga_query = text(
            """
            SELECT COUNT(DISTINCT manga_id)
            FROM favorites
            WHERE user_id IN :similar_users
            """
        )
        unique_manga_count = db.execute(
            unique_manga_query, {"similar_users": tuple(similar_users)}
        ).scalar()

        print(f"   Similar users have {unique_manga_count} unique mangas")
        print(f"   Found {len(recommendations)} recommendations after filtering user favorites")

        if len(recommendations) == 0:
            print(f"   Trying tag-based fallback")
            return self.tag_based_recommendations(user_id, db, limit)

        return recommendations
