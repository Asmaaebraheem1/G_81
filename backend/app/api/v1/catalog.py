"""Public catalog and content endpoints."""

from __future__ import annotations

from app.api.v1.blueprint import TAG_CATALOG, TAG_CONTENT, api_v1
from app.api.v1.schemas import (
    AlternativeQuery,
    ArticleQuery,
    FactorQuery,
    IdPath,
    SlugPath,
)
from app.core.errors import success
from app.modules.catalog import service


@api_v1.get("/categories", tags=[TAG_CATALOG], summary="Active categories")
def categories():
    return success(service.list_categories())


@api_v1.get("/categories/<int:id>", tags=[TAG_CATALOG], summary="Category detail")
def category_detail(path: IdPath):
    return success(service.get_category(path.id))


@api_v1.get("/factors", tags=[TAG_CATALOG], summary="Active emission factors")
def factors(query: FactorQuery):
    return success(service.list_factors(query.category_id, query.q))


@api_v1.get("/factors/<int:id>", tags=[TAG_CATALOG], summary="Factor detail + source")
def factor_detail(path: IdPath):
    return success(service.get_factor(path.id))


@api_v1.get("/alternatives", tags=[TAG_CATALOG], summary="Curated alternatives")
def alternatives(query: AlternativeQuery):
    return success(service.list_alternatives(query.category_id))


@api_v1.get("/alternatives/<int:id>", tags=[TAG_CATALOG], summary="Alternative detail")
def alternative_detail(path: IdPath):
    return success(service.get_alternative(path.id))


@api_v1.get("/content/articles", tags=[TAG_CONTENT], summary="Published articles")
def articles(query: ArticleQuery):
    return success(service.list_articles(query.category, query.q))


@api_v1.get("/content/articles/<slug>", tags=[TAG_CONTENT], summary="Article detail")
def article_detail(path: SlugPath):
    return success(service.get_article(path.slug))
