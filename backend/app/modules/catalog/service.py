"""Catalog and public content service."""

from __future__ import annotations

from sqlalchemy import or_

from app.core.db import db
from app.core.errors import ApiError
from app.modules.alternatives.models import Alternative
from app.modules.catalog.models import EmissionCategory, EmissionFactor
from app.modules.content.models import Article


def list_categories(active_only: bool = True) -> list[dict]:
    query = EmissionCategory.query
    if active_only:
        query = query.filter_by(is_active=True)
    return [category.to_dict() for category in query.order_by(EmissionCategory.sort_order).all()]


def get_category(category_id: int) -> dict:
    category = db.session.get(EmissionCategory, category_id)
    if category is None or not category.is_active:
        raise ApiError("not_found", "Category not found.", 404)
    return category.to_dict()


def list_factors(category_id: int | None = None, q: str | None = None) -> list[dict]:
    query = EmissionFactor.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                EmissionFactor.name_en.ilike(like),
                EmissionFactor.name_ar.ilike(like),
                EmissionFactor.key.ilike(like),
                EmissionFactor.activity_type.ilike(like),
            )
        )
    return [factor.to_dict() for factor in query.order_by(EmissionFactor.name_en).all()]


def get_factor(factor_id: int) -> dict:
    factor = db.session.get(EmissionFactor, factor_id)
    if factor is None or not factor.is_active:
        raise ApiError("not_found", "Emission factor not found.", 404)
    return factor.to_dict()


def list_alternatives(category_id: int | None = None) -> list[dict]:
    query = Alternative.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    return [
        item.to_dict()
        for item in query.order_by(Alternative.sort_order, Alternative.title_en).all()
    ]


def get_alternative(alternative_id: int) -> dict:
    item = db.session.get(Alternative, alternative_id)
    if item is None or not item.is_active:
        raise ApiError("not_found", "Alternative not found.", 404)
    return item.to_dict()


def list_articles(category: str | None = None, q: str | None = None) -> list[dict]:
    query = Article.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Article.title_en.ilike(like),
                Article.title_ar.ilike(like),
                Article.summary_en.ilike(like),
                Article.summary_ar.ilike(like),
            )
        )
    return [
        article.to_dict()
        for article in query.order_by(
            Article.sort_order, Article.published_at.desc(), Article.id.desc()
        ).all()
    ]


def get_article(slug: str) -> dict:
    article = Article.query.filter_by(slug=slug, is_published=True).first()
    if article is None:
        raise ApiError("not_found", "Article not found.", 404)
    return article.to_dict()
