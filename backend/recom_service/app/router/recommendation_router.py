from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config.database import get_db
from app.service.kmeans_service import KMeansRecommender
from typing import List
import json

router = APIRouter()

recommender = None


def get_recommender(db: Session, force_retrain: bool = False) -> KMeansRecommender:
    global recommender

    if recommender is None or force_retrain:
        cursor = db.execute(text("SELECT COUNT(DISTINCT user_id) FROM favorites"))
        user_count = cursor.scalar() or 0

        if user_count < 2:
            recommender = KMeansRecommender(n_clusters=2)
            return recommender

        n_clusters = min(max(2, user_count // 3), 5) if user_count >= 2 else 2

        recommender = KMeansRecommender(n_clusters=n_clusters)
        success = recommender.train(db)
        if not success and user_count > 0:
            recommender = KMeansRecommender(n_clusters=min(2, user_count))
            recommender.train(db)

    return recommender


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    global recommender

    try:
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        favorite_count = db.execute(text("SELECT COUNT(*) FROM favorites")).scalar()
        manga_count = db.execute(text("SELECT COUNT(*) FROM mangas")).scalar()
        users_with_favorites = db.execute(text("SELECT COUNT(DISTINCT user_id) FROM favorites")).scalar()
        demo_users_count = db.execute(text("SELECT COUNT(*) FROM users WHERE username LIKE 'demo_user_%'")).scalar()
        demo_users_with_favorites = db.execute(
            text(
                """
            SELECT COUNT(DISTINCT u.id)
            FROM users u
            JOIN favorites f ON u.id = f.user_id
            WHERE u.username LIKE 'demo_user_%'
        """
            )
        ).scalar()

        stats = {
            "total_users": user_count,
            "total_favorites": favorite_count,
            "total_mangas": manga_count,
            "users_with_favorites": users_with_favorites,
            "demo_users_count": demo_users_count,
            "demo_users_with_favorites": demo_users_with_favorites,
            "model_trained": recommender is not None and recommender.kmeans is not None,
        }

        if recommender and recommender.kmeans:
            stats.update(
                {
                    "clusters": recommender.n_clusters,
                    "users_in_model": len(recommender.user_clusters),
                    "cluster_distribution": {},
                }
            )

            for cluster_id in range(recommender.n_clusters):
                count = sum(1 for c in recommender.user_clusters.values() if c == cluster_id)
                stats["cluster_distribution"][f"cluster_{cluster_id}"] = count
        else:
            stats["training_message"] = (
                f"Need at least 2 users with favorites. Currently: {users_with_favorites}"
            )

        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}",
        )


@router.get("/{user_id}")
async def get_recommendations(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    try:
        user_check = db.execute(
            text("SELECT id FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).fetchone()

        if not user_check:
            raise HTTPException(status_code=404, detail="User not found")

        cursor = db.execute(
            text("SELECT COUNT(*) FROM favorites WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        user_fav_count = cursor.scalar() or 0

        if user_fav_count == 0:
            return {
                "user_id": user_id,
                "recommendations": [],
                "message": "Add some favorites first to get recommendations!",
            }

        cursor = db.execute(text("SELECT COUNT(DISTINCT user_id) FROM favorites"))
        current_user_count = cursor.scalar() or 0

        rec = get_recommender(db)

        needs_retrain = (
            rec.kmeans is None
            or user_id not in rec.user_clusters
            or current_user_count != len(rec.user_clusters)
            or current_user_count > len(rec.user_clusters)
        )

        if needs_retrain:
            rec = get_recommender(db, force_retrain=True)

        manga_ids: List[int] = []
        if rec.kmeans is not None and user_id in rec.user_clusters:
            manga_ids = rec.get_recommendations(user_id, db, limit)

        if not manga_ids:
            manga_ids = KMeansRecommender.tag_based_recommendations(user_id, db, limit)

        if not manga_ids:
            return {
                "user_id": user_id,
                "recommendations": [],
                "message": "No new recommendations found. Try exploring different mangas!",
            }

        if len(manga_ids) == 1:
            query = text(
                """
                SELECT id, title, description, rating, year, tags, cover
                FROM mangas
                WHERE id = :manga_id
            """
            )
            result = db.execute(query, {"manga_id": manga_ids[0]})
        else:
            query = text(
                """
                SELECT id, title, description, rating, year, tags, cover
                FROM mangas
                WHERE id IN :manga_ids
            """
            )
            result = db.execute(query, {"manga_ids": tuple(manga_ids)})

        mangas = []
        for row in result.fetchall():
            tags = row[5]
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags.replace("'", '"'))
                except Exception:
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
            elif not isinstance(tags, list):
                tags = []

            mangas.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "rating": float(row[3]) if row[3] else None,
                    "year": row[4],
                    "tags": tags,
                    "cover": row[6],
                }
            )

        manga_dict = {m["id"]: m for m in mangas}
        ordered_mangas = [manga_dict[mid] for mid in manga_ids if mid in manga_dict]

        return {
            "user_id": user_id,
            "recommendations": ordered_mangas,
            "count": len(ordered_mangas),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}",
        )
