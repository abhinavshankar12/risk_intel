"""Initial schema for risk intelligence platform

Revision ID: 001
Revises: 
Create Date: 2025-11-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    
    # Create regions table
    op.create_table(
        'regions',
        sa.Column('region_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326), nullable=True),
        sa.Column('baseline_risk', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('baseline_risk >= 0 AND baseline_risk <= 1', name='baseline_risk_range'),
        sa.PrimaryKeyConstraint('region_id'),
        sa.UniqueConstraint('name')
    )
    
    # Create region_neighbors table
    op.create_table(
        'region_neighbors',
        sa.Column('region_id', sa.Integer(), nullable=False),
        sa.Column('neighbor_id', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Float(), server_default='1.0', nullable=True),
        sa.ForeignKeyConstraint(['neighbor_id'], ['regions.region_id'], ),
        sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], ),
        sa.PrimaryKeyConstraint('region_id', 'neighbor_id')
    )
    op.create_index('idx_region_neighbors_neighbor', 'region_neighbors', ['neighbor_id'], unique=False)
    op.create_index('idx_region_neighbors_region', 'region_neighbors', ['region_id'], unique=False)
    
    # Create incidents table
    op.create_table(
        'incidents',
        sa.Column('incident_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('region_id', sa.Integer(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('metadata_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('severity >= 0 AND severity <= 1', name='severity_range'),
        sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], ),
        sa.PrimaryKeyConstraint('incident_id')
    )
    op.create_index('idx_incidents_region_occurred', 'incidents', ['region_id', 'occurred_at'], unique=False)
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('event_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('region_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('expected_attendance', sa.Integer(), nullable=True),
        sa.Column('metadata_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], ),
        sa.PrimaryKeyConstraint('event_id')
    )
    op.create_index('idx_events_region_start', 'events', ['region_id', 'start_time'], unique=False)
    
    # Create content_signals table
    op.create_table(
        'content_signals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('region_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('violent_call_post_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_content_signals_region_date', 'content_signals', ['region_id', 'date'], unique=True)
    
    # Create region_features table
    op.create_table(
        'region_features',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('region_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('recent_incidents_7d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('recent_incidents_30d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('neighbor_incidents_7d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('neighbor_incidents_30d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('event_count_7d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('event_attendance_7d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_violent_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('baseline_risk', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('features_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_region_features_region_date', 'region_features', ['region_id', 'date'], unique=True)
    
    # Create models table
    op.create_table(
        'models',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('algorithm', sa.String(length=50), nullable=False),
        sa.Column('metrics_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('config_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('model_path', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_version')
    )
    op.create_index('idx_models_active', 'models', ['active_flag'], unique=False)
    
    # Create risk_scores table
    op.create_table(
        'risk_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('region_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('p_raw', sa.Float(), nullable=False),
        sa.Column('r_smoothed', sa.Float(), nullable=False),
        sa.Column('risk_tier', sa.String(length=20), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('neighbor_avg_p', sa.Float(), nullable=True),
        sa.Column('prev_r', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('p_raw >= 0 AND p_raw <= 1', name='p_raw_range'),
        sa.CheckConstraint('r_smoothed >= 0', name='r_smoothed_positive'),
        sa.CheckConstraint("risk_tier IN ('low', 'medium', 'high')", name='risk_tier_values'),
        sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_risk_scores_date', 'risk_scores', ['date'], unique=False)
    op.create_index('idx_risk_scores_region_date', 'risk_scores', ['region_id', 'date'], unique=False)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('payload_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action_type'], unique=False)
    op.create_index('idx_audit_logs_created', 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_audit_logs_created', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('idx_risk_scores_region_date', table_name='risk_scores')
    op.drop_index('idx_risk_scores_date', table_name='risk_scores')
    op.drop_table('risk_scores')
    
    op.drop_index('idx_models_active', table_name='models')
    op.drop_table('models')
    
    op.drop_index('idx_region_features_region_date', table_name='region_features')
    op.drop_table('region_features')
    
    op.drop_index('idx_content_signals_region_date', table_name='content_signals')
    op.drop_table('content_signals')
    
    op.drop_index('idx_events_region_start', table_name='events')
    op.drop_table('events')
    
    op.drop_index('idx_incidents_region_occurred', table_name='incidents')
    op.drop_table('incidents')
    
    op.drop_index('idx_region_neighbors_region', table_name='region_neighbors')
    op.drop_index('idx_region_neighbors_neighbor', table_name='region_neighbors')
    op.drop_table('region_neighbors')
    
    op.drop_table('regions')

