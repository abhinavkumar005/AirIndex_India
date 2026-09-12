"""Initial schema — Phase 2

Creates all 11 tables for reference data, evidence, observations,
methodology, and index outputs.

Revision ID: 001
Revises: None
Create Date: 2026-09-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Reference tables ---

    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cities")),
        sa.UniqueConstraint("code", name=op.f("uq_cities_code")),
    )

    op.create_table(
        "airports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("iata_code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_airports")),
        sa.UniqueConstraint("iata_code", name=op.f("uq_airports_iata_code")),
        sa.ForeignKeyConstraint(
            ["city_id"], ["cities.id"],
            name=op.f("fk_airports_city_id_cities"),
        ),
        sa.CheckConstraint(
            "length(iata_code) = 3",
            name=op.f("ck_airports_iata_code_length"),
        ),
    )

    op.create_table(
        "airlines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_airlines")),
        sa.UniqueConstraint("code", name=op.f("uq_airlines_code")),
        sa.CheckConstraint(
            "length(code) >= 2 AND length(code) <= 3",
            name=op.f("ck_airlines_airline_code_length"),
        ),
    )

    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("origin_id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_routes")),
        sa.UniqueConstraint("code", name=op.f("uq_routes_code")),
        sa.ForeignKeyConstraint(
            ["origin_id"], ["airports.id"],
            name=op.f("fk_routes_origin_id_airports"),
        ),
        sa.ForeignKeyConstraint(
            ["destination_id"], ["airports.id"],
            name=op.f("fk_routes_destination_id_airports"),
        ),
        sa.CheckConstraint(
            "origin_id != destination_id",
            name=op.f("ck_routes_origin_ne_destination"),
        ),
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("compliance_status", sa.String(length=50), nullable=False),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
        sa.UniqueConstraint("code", name=op.f("uq_sources_code")),
    )

    op.create_table(
        "source_connectors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("connector_version", sa.String(length=50), nullable=False),
        sa.Column("parser_version", sa.String(length=50), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_connectors")),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"],
            name=op.f("fk_source_connectors_source_id_sources"),
        ),
        sa.UniqueConstraint(
            "source_id", "connector_version", "parser_version",
            name="uq_source_connector_version",
        ),
    )

    # --- Methodology tables ---

    op.create_table(
        "route_weights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("config_version", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_route_weights")),
        sa.ForeignKeyConstraint(
            ["route_id"], ["routes.id"],
            name=op.f("fk_route_weights_route_id_routes"),
        ),
        sa.CheckConstraint("weight > 0", name=op.f("ck_route_weights_weight_positive")),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name=op.f("ck_route_weights_effective_date_order"),
        ),
    )

    # --- Evidence tables ---

    op.create_table(
        "fare_raw",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("request_metadata", sa.JSON(), nullable=True),
        sa.Column("connector_version", sa.String(length=50), nullable=False),
        sa.Column("parser_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fare_raw")),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"],
            name=op.f("fk_fare_raw_source_id_sources"),
        ),
    )

    # --- Observation tables ---

    op.create_table(
        "fare_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("origin_id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("airline_id", sa.Integer(), nullable=True),
        sa.Column("flight_number", sa.String(length=20), nullable=True),
        sa.Column("fare_class", sa.String(length=30), nullable=True),
        sa.Column("departure_date", sa.Date(), nullable=False),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("advance_purchase_days", sa.Integer(), nullable=False),
        sa.Column("base_fare", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("taxes", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("airport_charges", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("user_development_fee", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("convenience_fee", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("other_charges", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("total_payable_fare", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("availability_status", sa.String(length=20), nullable=False),
        sa.Column("cancellation_status", sa.String(length=20), nullable=False),
        sa.Column("quality_status", sa.String(length=20), nullable=False),
        sa.Column("quality_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("connector_version", sa.String(length=50), nullable=False),
        sa.Column("parser_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fare_observations")),
        sa.ForeignKeyConstraint(
            ["raw_id"], ["fare_raw.id"],
            name=op.f("fk_fare_observations_raw_id_fare_raw"),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"],
            name=op.f("fk_fare_observations_source_id_sources"),
        ),
        sa.ForeignKeyConstraint(
            ["origin_id"], ["airports.id"],
            name=op.f("fk_fare_observations_origin_id_airports"),
        ),
        sa.ForeignKeyConstraint(
            ["destination_id"], ["airports.id"],
            name=op.f("fk_fare_observations_destination_id_airports"),
        ),
        sa.ForeignKeyConstraint(
            ["airline_id"], ["airlines.id"],
            name=op.f("fk_fare_observations_airline_id_airlines"),
        ),
        sa.CheckConstraint(
            "origin_id != destination_id",
            name=op.f("ck_fare_observations_obs_origin_ne_destination"),
        ),
        sa.CheckConstraint(
            "advance_purchase_days >= 0",
            name=op.f("ck_fare_observations_advance_days_non_negative"),
        ),
        sa.CheckConstraint(
            "base_fare IS NULL OR base_fare >= 0",
            name=op.f("ck_fare_observations_base_fare_non_negative"),
        ),
        sa.CheckConstraint(
            "taxes IS NULL OR taxes >= 0",
            name=op.f("ck_fare_observations_taxes_non_negative"),
        ),
        sa.CheckConstraint(
            "airport_charges IS NULL OR airport_charges >= 0",
            name=op.f("ck_fare_observations_airport_charges_non_negative"),
        ),
        sa.CheckConstraint(
            "user_development_fee IS NULL OR user_development_fee >= 0",
            name=op.f("ck_fare_observations_udf_non_negative"),
        ),
        sa.CheckConstraint(
            "convenience_fee IS NULL OR convenience_fee >= 0",
            name=op.f("ck_fare_observations_convenience_fee_non_negative"),
        ),
        sa.CheckConstraint(
            "other_charges IS NULL OR other_charges >= 0",
            name=op.f("ck_fare_observations_other_charges_non_negative"),
        ),
        sa.CheckConstraint(
            "length(currency) = 3",
            name=op.f("ck_fare_observations_currency_iso_length"),
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)",
            name=op.f("ck_fare_observations_quality_score_range"),
        ),
    )

    op.create_index(
        "ix_obs_observed_source", "fare_observations",
        ["observed_at", "source_id"],
    )
    op.create_index(
        "ix_obs_route_departure", "fare_observations",
        ["origin_id", "destination_id", "departure_date"],
    )
    op.create_index(
        "ix_obs_departure_advance", "fare_observations",
        ["departure_date", "advance_purchase_days"],
    )
    op.create_index(
        "ix_obs_quality_status", "fare_observations",
        ["quality_status"],
    )

    # --- Output tables ---

    op.create_table(
        "index_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("index_value", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("base_period", sa.String(length=50), nullable=True),
        sa.Column("config_version", sa.String(length=100), nullable=False),
        sa.Column("calculation_version", sa.String(length=100), nullable=False),
        sa.Column("coverage_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("route_count", sa.Integer(), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_index_values")),
        sa.UniqueConstraint(
            "frequency", "period_start", "config_version",
            name="uq_index_freq_period_config",
        ),
    )

    op.create_table(
        "index_components",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("index_value_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("representative_fare", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("base_fare_ref", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("price_relative", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("weighted_contribution", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("excluded_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_index_components")),
        sa.ForeignKeyConstraint(
            ["index_value_id"], ["index_values.id"],
            name=op.f("fk_index_components_index_value_id_index_values"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["route_id"], ["routes.id"],
            name=op.f("fk_index_components_route_id_routes"),
        ),
    )


def downgrade() -> None:
    op.drop_table("index_components")
    op.drop_table("index_values")
    op.drop_index("ix_obs_quality_status", table_name="fare_observations")
    op.drop_index("ix_obs_departure_advance", table_name="fare_observations")
    op.drop_index("ix_obs_route_departure", table_name="fare_observations")
    op.drop_index("ix_obs_observed_source", table_name="fare_observations")
    op.drop_table("fare_observations")
    op.drop_table("fare_raw")
    op.drop_table("route_weights")
    op.drop_table("source_connectors")
    op.drop_table("sources")
    op.drop_table("routes")
    op.drop_table("airlines")
    op.drop_table("airports")
    op.drop_table("cities")
