"""Dashboard and report endpoints."""

from __future__ import annotations

from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_REPORTS, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import ExportQuery, ReportQuery, TopActivitiesQuery, TrendQuery
from app.core.errors import success
from app.modules.reports import service


@api_v1.get("/dashboard/summary", tags=[TAG_REPORTS], summary="Dashboard totals")
@jwt_required()
def dashboard(query: ReportQuery):
    return success(
        service.dashboard(
            current_user(),
            query.period,
            query.from_date,
            query.to_date,
        )
    )


@api_v1.get("/reports/summary", tags=[TAG_REPORTS], summary="Period report")
@jwt_required()
def report_summary(query: ReportQuery):
    return success(
        service.report_summary(
            current_user(),
            query.period,
            query.from_date,
            query.to_date,
        )
    )


@api_v1.get("/reports/trend", tags=[TAG_REPORTS], summary="Monthly trend")
@jwt_required()
def report_trend(query: TrendQuery):
    return success(service.trend(current_user(), query.months))


@api_v1.get("/reports/categories", tags=[TAG_REPORTS], summary="Category totals + shares")
@jwt_required()
def report_categories(query: ReportQuery):
    return success(
        service.categories(
            current_user(),
            query.period,
            query.from_date,
            query.to_date,
        )
    )


@api_v1.get(
    "/reports/top-activities",
    tags=[TAG_REPORTS],
    summary="Highest-emission activities",
)
@jwt_required()
def report_top_activities(query: TopActivitiesQuery):
    return success(
        service.top_activities(
            current_user(),
            query.period,
            query.from_date,
            query.to_date,
            query.limit,
        )
    )


@api_v1.get("/reports/comparison", tags=[TAG_REPORTS], summary="Current vs previous period")
@jwt_required()
def report_comparison(query: ReportQuery):
    return success(
        service.comparison(
            current_user(),
            query.period,
            query.from_date,
            query.to_date,
        )
    )


@api_v1.get("/reports/export.csv", tags=[TAG_REPORTS], summary="CSV export")
@jwt_required()
def report_export(query: ExportQuery):
    return service.export_csv(current_user(), query.from_date, query.to_date)
