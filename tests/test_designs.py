"""A design changes presentation only after the settings release workflow."""

import pytest

from conftest import action


DESIGNS = ('studio', 'noir', 'editorial', 'atelier', 'aurora',
           'brutalist', 'minimal', 'garden', 'sunset', 'terminal')


@pytest.mark.parametrize('design', DESIGNS)
def test_designs_follow_published_settings(admin, design):
    row = admin.get('/api/admin/content?kind=settings').json()[0]
    assert 'data-design="studio"' in admin.get('/').text
    response = admin.patch(f"/api/admin/content/{row['id']}", json={
        'expected_revision': row['revision'],
        'data': {**row['data'], 'design': design},
    })
    assert response.status_code == 200, response.text
    row = response.json()
    assert 'data-design="studio"' in admin.get('/').text
    action(admin, row, 'publish')
    page = admin.get('/')
    assert page.status_code == 200
    assert f'data-design="{design}"' in page.text
    assert '/static/css/designs.css' in page.text
    assert 'FORM / STUDIO' in page.text


def test_unknown_design_is_rejected(admin):
    row = admin.get('/api/admin/content?kind=settings').json()[0]
    response = admin.patch(
        f"/api/admin/content/{row['id']}",
        json={'expected_revision': row['revision'],
              'data': {**row['data'], 'design': 'injected-class-name'}},
    )
    assert response.status_code == 422
    assert 'data-design="studio"' in admin.get('/').text
