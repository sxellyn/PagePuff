from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.model.manga_model import Manga
from app.schema.manga_schema import MangaResponse
from typing import List

router = APIRouter()

@router.get("/mangas", response_model=List[MangaResponse])
def list_mangas(db: Session = Depends(get_db)):
    try:
        mangas = db.query(Manga).all()
        manga_list = []
        
        for manga in mangas:
            try:
                # Verificar se os dados básicos são válidos
                if not manga.title:
                    continue  # Pular mangás sem título
                
                manga_dict = {
                    "id": manga.id,
                    "title": manga.title,
                    "description": manga.description or "",
                    "rating": float(manga.rating) if manga.rating else 0.0,
                    "year": int(manga.year) if manga.year else 0,
                    "cover": manga.cover or ""
                }
                                # Tratar tags de forma robusta (pode ser JSON ou ARRAY)
                try:
                    print(f"🔍 Processando tags do manga {manga.id} ({manga.title}):")
                    print(f"   - Tipo das tags: {type(manga.tags)}")
                    print(f"   - Valor das tags: {manga.tags}")

                    if manga.tags and isinstance(manga.tags, str):
                        # Se for string, tentar fazer parse JSON ai
                        import json
                        # Remover aspas simples extras que podem estar no formato Python
                        cleaned_tags = manga.tags.replace("'", '"')
                        parsed_tags = json.loads(cleaned_tags)
                        print(f"   - Tags parseadas de string: {parsed_tags}")
                        manga_dict["tags"] = parsed_tags
                    elif manga.tags and isinstance(manga.tags, list):
                        # Se for lista, usar diretamente
                        print(f"   - Tags já são lista: {manga.tags}")
                        manga_dict["tags"] = manga.tags
                    elif manga.tags is None:
                        print(f"   - Tags são None, definindo como array vazio")
                        manga_dict["tags"] = []
                    else:
                        print(f"   - Tags têm tipo inesperado: {type(manga.tags)}, definindo como array vazio")
                        manga_dict["tags"] = []

                    print(f"   - Tags finais: {manga_dict['tags']}")

                except Exception as tag_error:
                    print(f"   - ❌ Erro ao processar tags: {tag_error}")
                    print(f"   - Definindo tags como array vazio")
                    manga_dict["tags"] = []
                
                manga_list.append(manga_dict)
                
            except Exception as manga_error:
                print(f"Erro ao processar manga {manga.id}: {manga_error}")
                continue  # Pular mangás com erro
        
        print(f"Total de mangás processados com sucesso: {len(manga_list)}")
        return manga_list
        
    except Exception as e:
        print(f"Erro ao listar mangás: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/mangas/{manga_id}", response_model=MangaResponse)
def get_manga_by_id(manga_id: int, db: Session = Depends(get_db)):
    try:
        manga = db.query(Manga).filter(Manga.id == manga_id).first()
        if not manga:
            raise HTTPException(status_code=404, detail="Manga not found")
        
        # Converter para dicionário para evitar problemas com JSON
        manga_dict = {
            "id": manga.id,
            "title": manga.title,
            "description": manga.description,
            "rating": manga.rating,
            "year": manga.year,
            "cover": manga.cover
        }
        
        # Tratar tags de forma robusta (pode ser JSON ou ARRAY)
        try:
            if manga.tags and isinstance(manga.tags, str):
                # Se for string, tentar fazer parse JSON
                import json
                manga_dict["tags"] = json.loads(manga.tags)
            elif manga.tags and isinstance(manga.tags, list):
                # Se for lista, usar diretamente
                manga_dict["tags"] = manga.tags
            else:
                manga_dict["tags"] = []
        except:
            manga_dict["tags"] = []
        
        return manga_dict
    except Exception as e:
        print(f"Erro ao buscar manga {manga_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
