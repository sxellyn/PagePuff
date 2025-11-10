import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MangaRecommendationService:
    def __init__(self, n_clusters: int = 8):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.scaler = StandardScaler()
        self.tag_binarizer = MultiLabelBinarizer()
        self.manga_features = None
        self.cluster_centers = None
        self.manga_clusters = None
        
    def preprocess_manga_data(self, mangas: List[Dict]) -> pd.DataFrame:
        """Preprocessa os dados dos mangas para clustering"""
        logger.info(f"Preprocessando {len(mangas)} mangas...")
        
        # Converter para DataFrame
        df = pd.DataFrame(mangas)
        
        # Processar tags
        df['tags_processed'] = df['tags'].apply(lambda x: x if isinstance(x, list) else [])
        
        # Criar features numéricas
        features = []
        
        for _, manga in df.iterrows():
            feature_vector = []
            
            # Rating (normalizado 0-1)
            rating = manga.get('rating', 0) or 0
            feature_vector.append(rating / 5.0)  # Normalizar para 0-1
            
            # Year (normalizado 0-1, considerando range 1950-2025)
            year = manga.get('year', 2000) or 2000
            year_normalized = (year - 1950) / (2025 - 1950) if year else 0.5
            feature_vector.append(max(0, min(1, year_normalized)))
            
            # Número de tags
            tags_count = len(manga.get('tags_processed', []))
            feature_vector.append(min(tags_count / 10.0, 1.0))  # Normalizar para 0-1
            
            features.append(feature_vector)
        
        # Converter para numpy array
        features_array = np.array(features)
        
        # Aplicar scaling
        features_scaled = self.scaler.fit_transform(features_array)
        
        # Processar tags para one-hot encoding
        all_tags = []
        for manga in mangas:
            tags = manga.get('tags', [])
            if isinstance(tags, list):
                all_tags.extend(tags)
        
        unique_tags = list(set(all_tags))
        logger.info(f"Encontradas {len(unique_tags)} tags únicas")
        
        # Criar matriz de tags (one-hot encoding)
        tag_matrix = np.zeros((len(mangas), len(unique_tags)))
        
        for i, manga in enumerate(mangas):
            tags = manga.get('tags', [])
            if isinstance(tags, list):
                for tag in tags:
                    if tag in unique_tags:
                        tag_idx = unique_tags.index(tag)
                        tag_matrix[i, tag_idx] = 1
        
        # Combinar features numéricas com tags
        combined_features = np.hstack([features_scaled, tag_matrix])
        
        logger.info(f"Features combinadas: {combined_features.shape}")
        return combined_features, unique_tags
    
    def train_clustering_model(self, mangas: List[Dict]) -> None:
        """Treina o modelo de clustering K-means"""
        logger.info("Treinando modelo de clustering K-means...")
        
        # Preprocessar dados
        features, unique_tags = self.preprocess_manga_data(mangas)
        self.manga_features = features
        
        # Treinar K-means
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.manga_clusters = self.kmeans.fit_predict(features)
        self.cluster_centers = self.kmeans.cluster_centers_
        
        logger.info(f"Modelo treinado com {self.n_clusters} clusters")
        
        # Log das estatísticas dos clusters
        for i in range(self.n_clusters):
            cluster_size = np.sum(self.manga_clusters == i)
            logger.info(f"Cluster {i}: {cluster_size} mangas")
    
    def get_user_preferences(self, user_favorites: List[Dict], mangas: List[Dict]) -> np.ndarray:
        """Extrai as preferências do usuário baseado nos favoritos"""
        if not user_favorites:
            return None
        
        # Encontrar os mangas favoritos
        favorite_manga_ids = [fav['manga_id'] for fav in user_favorites]
        favorite_mangas = [m for m in mangas if m['id'] in favorite_manga_ids]
        
        if not favorite_mangas:
            return None
        
        # Calcular o perfil médio dos favoritos
        favorite_features = []
        for manga in favorite_mangas:
            try:
                manga_idx = next(i for i, m in enumerate(mangas) if m['id'] == manga['id'])
                if manga_idx < len(self.manga_features):
                    favorite_features.append(self.manga_features[manga_idx])
            except (StopIteration, IndexError):
                continue
        
        if not favorite_features:
            return None
        
        # Retornar o centroide dos favoritos
        return np.mean(favorite_features, axis=0)
    
    def get_recommendations(self, user_id: int, user_favorites: List[Dict], 
                           mangas: List[Dict], limit: int = 10, user_preferences: Dict = None) -> List[Dict]:
        """Gera recomendações personalizadas para o usuário usando favoritos E preferências"""
        logger.info(f"Gerando recomendações para usuário {user_id}")
        
        if not self.kmeans:
            logger.error("Modelo de clustering não foi treinado")
            return []
        
        # Se não tem favoritos nem preferências, retornar mangas populares
        if not user_favorites and not user_preferences:
            logger.info("Usuário não tem favoritos nem preferências, retornando mangas populares")
            return self._get_popular_mangas(mangas, limit)
        
        # Obter perfis do usuário baseado em favoritos E preferências
        user_profiles = []
        
        # 1. Perfil baseado nos favoritos
        if user_favorites:
            favorite_profile = self.get_user_preferences(user_favorites, mangas)
            if favorite_profile is not None:
                user_profiles.append(favorite_profile)
                logger.info(f"Perfil baseado em {len(user_favorites)} favoritos adicionado")
        
        # 2. Perfil baseado nas preferências do onboarding
        if user_preferences:
            preference_profile = self._get_profile_from_preferences(user_preferences, mangas)
            if preference_profile is not None:
                user_profiles.append(preference_profile)
                logger.info(f"Perfil baseado em {len(user_preferences.get('preferred_genres', []))} gêneros adicionado")
        
        if not user_profiles:
            logger.info("Não foi possível gerar perfil do usuário, retornando mangas populares")
            return self._get_popular_mangas(mangas, limit)
        
        # Combinar os perfis (média ponderada: favoritos têm peso maior)
        if len(user_profiles) == 2:
            # 70% favoritos + 30% preferências
            combined_profile = 0.7 * user_profiles[0] + 0.3 * user_profiles[1]
            logger.info("Perfil combinado: 70% favoritos + 30% preferências")
        else:
            # Usar o único perfil disponível
            combined_profile = user_profiles[0]
            logger.info("Usando perfil único disponível")
        
        # Encontrar os clusters mais próximos do perfil combinado
        distances = []
        for i, center in enumerate(self.cluster_centers):
            distance = np.linalg.norm(combined_profile - center)
            distances.append((i, distance))
        
        # Ordenar por distância (menor = mais similar)
        distances.sort(key=lambda x: x[1])
        preferred_clusters = [cluster_id for cluster_id, _ in distances[:3]]  # Top 3 clusters
        
        logger.info(f"Clusters preferidos: {preferred_clusters}")
        
        # Filtrar mangas dos clusters preferidos
        recommended_mangas = []
        for manga_idx, cluster_id in enumerate(self.manga_clusters):
            if cluster_id in preferred_clusters:
                manga = mangas[manga_idx]
                
                # Verificar se não está nos favoritos
                if not user_favorites or manga['id'] not in [fav['manga_id'] for fav in user_favorites]:
                    recommendation = {
                        **manga,
                        'cluster_id': int(cluster_id)
                    }
                    recommended_mangas.append(recommendation)
        
        # Se não encontrou mangas suficientes nos clusters preferidos, adicionar mangas populares
        if len(recommended_mangas) < limit:
            popular_mangas = self._get_popular_mangas(mangas, limit - len(recommended_mangas))
            # Remover duplicatas
            existing_ids = {m['id'] for m in recommended_mangas}
            for manga in popular_mangas:
                if manga['id'] not in existing_ids:
                    recommended_mangas.append(manga)
        
        # Limitar o número de recomendações
        final_recommendations = recommended_mangas[:limit]
        
        logger.info(f"Geradas {len(final_recommendations)} recomendações para usuário {user_id}")
        genres_count = len(user_preferences.get('preferred_genres', [])) if user_preferences else 0
        logger.info(f"Baseado em: {len(user_favorites)} favoritos + {genres_count} gêneros preferidos")
        
        return final_recommendations
    
    def _get_profile_from_preferences(self, user_preferences: Dict, mangas: List[Dict]) -> np.ndarray:
        """Gera perfil do usuário baseado em suas preferências iniciais"""
        try:
            # Criar vetor de preferências baseado nos gêneros
            preferred_genres = user_preferences.get('preferred_genres', [])
            
            # Filtrar mangas que têm pelo menos um gênero preferido
            preferred_mangas = []
            for manga in mangas:
                manga_tags = manga.get('tags', [])
                if isinstance(manga_tags, list):
                    if any(genre in manga_tags for genre in preferred_genres):
                        preferred_mangas.append(manga)
            
            if not preferred_mangas:
                return None
            
            # Calcular perfil médio dos mangas preferidos
            preferred_indices = []
            for manga in preferred_mangas:
                try:
                    # Verificar se o índice está dentro dos limites
                    manga_idx = next(i for i, m in enumerate(mangas) if m['id'] == manga['id'])
                    if manga_idx < len(self.manga_features):
                        preferred_indices.append(manga_idx)
                except (StopIteration, IndexError):
                    # Pular mangas com problemas de índice
                    continue
            
            if not preferred_indices:
                return None
            
            # Retornar o centroide dos mangas preferidos
            return np.mean(self.manga_features[preferred_indices], axis=0)
            
        except Exception as e:
            logger.error(f"Erro ao gerar perfil das preferências: {e}")
            return None
    
    def _get_popular_mangas(self, mangas: List[Dict], limit: int) -> List[Dict]:
        """Retorna mangas populares baseado em rating"""
        popular_mangas = []
        
        for manga in mangas:
            if manga.get('rating') and manga.get('rating') >= 4.0:
                recommendation = {
                    **manga,
                    'cluster_id': -1  # Cluster especial para populares
                }
                popular_mangas.append(recommendation)
        
        # Ordenar por rating
        popular_mangas.sort(key=lambda x: x.get('rating', 0), reverse=True)
        return popular_mangas[:limit]
    
    def get_cluster_info(self, mangas: List[Dict]) -> List[Dict]:
        """Retorna informações sobre os clusters"""
        if not self.kmeans:
            return []
        
        cluster_info = []
        
        for cluster_id in range(self.n_clusters):
            # Mangas neste cluster
            cluster_manga_indices = np.where(self.manga_clusters == cluster_id)[0]
            cluster_mangas = [mangas[i] for i in cluster_manga_indices]
            
            if not cluster_mangas:
                continue
            
            # Estatísticas do cluster
            ratings = [m.get('rating', 0) or 0 for m in cluster_mangas]
            avg_rating = np.mean(ratings) if ratings else 0
            
            # Tags mais comuns
            all_tags = []
            for manga in cluster_mangas:
                tags = manga.get('tags', [])
                if isinstance(tags, list):
                    all_tags.extend(tags)
            
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            common_tags = [tag for tag, count in common_tags]
            
            # Mangas representativos (maior rating)
            representative_mangas = sorted(cluster_mangas, key=lambda x: x.get('rating', 0) or 0, reverse=True)[:3]
            representative_titles = [m.get('title', '') for m in representative_mangas]
            
            cluster_info.append({
                'cluster_id': int(cluster_id),
                'size': len(cluster_mangas),
                'avg_rating': round(avg_rating, 2),
                'common_tags': common_tags,
                'representative_mangas': representative_titles
            })
        
        return cluster_info
