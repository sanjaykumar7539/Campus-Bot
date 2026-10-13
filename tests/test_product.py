from pathlib import Path

from src.product.product_info import get_product_info, get_product_status
from src.product.analytics import ProductAnalytics
from src.database.db_manager import DatabaseManager


def test_product_info_has_separate_product_and_tenant_identity():
    info = get_product_info()
    assert info['product_name']
    assert info['product_version']
    assert info['institute_name']
    assert 'auto_pdf_ingestion' in info['features']


def test_product_status_has_component_readiness():
    status = get_product_status()
    assert status['install_id'].startswith('inst_')
    assert 'components' in status
    assert 'chat_ready' in status


def test_local_analytics_empty_database(tmp_path):
    db = DatabaseManager(str(tmp_path / 'analytics.db'))
    data = ProductAnalytics(db).summary()
    assert data['sessions'] == 0
    assert data['user_messages'] == 0
    assert data['feedback_total'] == 0
    assert data['positive_feedback_rate'] is None
