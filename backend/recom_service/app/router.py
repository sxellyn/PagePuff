from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import requests
import asyncio
from app.schemas import RecommendationRequest, RecommendationResponse, ClusterInfo, UserPreferences, PreferencesResponse
from app.recommendation_service import MangaRecommendationService

router = APIRouter()

# Instância global do serviço de recomendação
recommendation_service = MangaRecommendationService(n_clusters=8)

# Cache para dados dos mangas e favoritos
manga_cache = []
favorites_cache = {}
user_preferences = {}  # Cache para preferências dos usuários

def fetch_manga_data():
    """Busca dados dos mangas do manga service"""
    try:
        response = requests.get("http://manga_service:8000/mangas")
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=500, detail="Erro ao buscar dados dos mangas")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar com manga service: {str(e)}")

def fetch_user_favorites(user_id: int):
    """Busca favoritos de um usuário específico"""
    try:
        response = requests.get(f"http://user_service:8000/user/favorites", 
                             headers={"Authorization": f"Bearer user_{user_id}"})
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Erro ao buscar favoritos do usuário {user_id}: {e}")
        return []

@router.post("/preferences", response_model=PreferencesResponse)
async def save_user_preferences(preferences: UserPreferences, background_tasks: BackgroundTasks):
    """Salva preferências iniciais do usuário e inicia treinamento do modelo"""
    global manga_cache
    
    try:
        # Salvar preferências do usuário
        user_preferences[preferences.user_id] = preferences.dict()
        
        # Buscar dados dos mangas se não estiverem em cache
        if not manga_cache:
            mangas = fetch_manga_data()
            manga_cache = mangas
        
        # Iniciar treinamento do modelo em background
        background_tasks.add_task(train_model_with_preferences, preferences.user_id, preferences)
        
        return PreferencesResponse(
            message="Preferências salvas com sucesso! Modelo de recomendação sendo treinado em background.",
            user_id=preferences.user_id,
            preferences_saved=True,
            model_training_started=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar preferências: {str(e)}")

def train_model_with_preferences(user_id: int, preferences: UserPreferences):
    """Treina o modelo considerando as preferências do usuário"""
    try:
        print(f"🔄 Treinando modelo com preferências do usuário {user_id}...")
        
        # Filtrar mangas baseado nas preferências
        filtered_mangas = []
        for manga in manga_cache:
            # Verificar se tem pelo menos um gênero preferido
            manga_tags = manga.get('tags', [])
            if isinstance(manga_tags, list):
                has_preferred_genre = any(genre in manga_tags for genre in preferences.preferred_genres)
                if has_preferred_genre:
                    filtered_mangas.append(manga)
        
        if not filtered_mangas:
            print(f"⚠️ Nenhum manga encontrado com os gêneros preferidos do usuário {user_id}")
            # Usar todos os mangas se não encontrar nenhum com os gêneros preferidos
            filtered_mangas = manga_cache
        
        # Treinar o modelo
        recommendation_service.train_clustering_model(filtered_mangas)
        print(f"✅ Modelo treinado com sucesso para usuário {user_id}!")
        
    except Exception as e:
        print(f"❌ Erro ao treinar modelo com preferências: {e}")

@router.post("/train", response_model=dict)
async def train_recommendation_model(background_tasks: BackgroundTasks):
    """Treina o modelo de recomendação em background"""
    try:
        # Buscar dados dos mangas
        mangas = fetch_manga_data()
        
        if not mangas:
            raise HTTPException(status_code=500, detail="Nenhum manga encontrado")
        
        # Treinar o modelo em background
        background_tasks.add_task(train_model_background, mangas)
        
        return {
            "message": "Modelo de recomendação iniciado em background",
            "total_mangas": len(mangas),
            "status": "training"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao treinar modelo: {str(e)}")

def train_model_background(mangas: List[dict]):
    """Função para treinar o modelo em background"""
    global manga_cache
    
    try:
        print(f"🔄 Treinando modelo com {len(mangas)} mangas...")
        recommendation_service.train_clustering_model(mangas)
        print("✅ Modelo treinado com sucesso!")
        
        # Atualizar cache
        manga_cache = mangas
        
    except Exception as e:
        print(f"❌ Erro ao treinar modelo: {e}")

@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """Gera recomendações personalizadas para um usuário"""
    try:
        # Verificar se o modelo foi treinado
        if not recommendation_service.kmeans:
            raise HTTPException(status_code=400, detail="Modelo de recomendação não foi treinado. Execute /train primeiro.")
        
        # Verificar se há dados no cache
        if not manga_cache:
            raise HTTPException(status_code=400, detail="Cache de mangas vazio. Execute /refresh-cache primeiro.")
        
        # Buscar favoritos do usuário
        user_favorites = fetch_user_favorites(request.user_id)
        
        # Buscar preferências do usuário
        user_prefs = user_preferences.get(request.user_id, None)
        
        # Gerar recomendações
        recommendations = recommendation_service.get_recommendations(
            user_id=request.user_id,
            user_favorites=user_favorites,
            mangas=manga_cache,
            limit=request.limit,
            user_preferences=user_prefs
        )
        
        return RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            total_recommendations=len(recommendations)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Erro ao gerar recomendações: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/clusters", response_model=List[ClusterInfo])
async def get_cluster_info():
    """Retorna informações sobre os clusters"""
    try:
        # Verificar se o modelo foi treinado
        if not recommendation_service.kmeans:
            raise HTTPException(status_code=400, detail="Modelo de recomendação não foi treinado")
        
        # Verificar se há dados no cache
        if not manga_cache:
            raise HTTPException(status_code=400, detail="Cache de mangas vazio. Execute /refresh-cache primeiro.")
        
        # Verificar se os atributos necessários existem
        if not hasattr(recommendation_service, 'manga_clusters') or recommendation_service.manga_clusters is None:
            raise HTTPException(status_code=400, detail="Modelo de clustering não foi inicializado corretamente")
        
        cluster_info = recommendation_service.get_cluster_info(manga_cache)
        return cluster_info
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Erro ao obter informações dos clusters: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/status")
async def get_service_status():
    """Retorna o status do serviço de recomendação"""
    return {
        "status": "healthy",
        "model_trained": recommendation_service.kmeans is not None,
        "total_clusters": recommendation_service.n_clusters if recommendation_service.kmeans else 0,
        "manga_cache_size": len(manga_cache),
        "favorites_cache_size": len(favorites_cache),
        "users_with_preferences": len(user_preferences)
    }

@router.post("/refresh-cache")
async def refresh_cache():
    """Atualiza o cache de dados"""
    global manga_cache
    
    try:
        # Atualizar cache de mangas
        mangas = fetch_manga_data()
        manga_cache = mangas
        
        return {
            "message": "Cache atualizado com sucesso",
            "total_mangas": len(mangas)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cache: {str(e)}")
