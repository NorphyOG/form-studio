from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

PASSWORD='A-long-test-password-2026!'

@pytest.fixture
def app(tmp_path):
    return create_app(Settings(tmp_path,origin='http://testserver'))

@pytest.fixture
def client(app):
    with TestClient(app,headers={'Origin':'http://testserver'}) as c:
        yield c

@pytest.fixture
def admin(client,app):
    body=dict(setup_key=(app.state.db.data_dir/'.setup-key').read_text(),name='Admin Test',email='admin@example.test',password=PASSWORD)
    response=client.post('/api/setup',json=body)
    assert response.status_code==200,response.text
    session=client.get('/api/admin/session').json()
    client.headers['X-CSRF-Token']=session['csrf']
    return client

@pytest.fixture
def account(app,admin):
    clients=[]
    def make(role):
        email=role+'@example.test'
        response=admin.post('/api/admin/users',json=dict(name=role.title()+' Test',email=email,password=PASSWORD,role=role))
        assert response.status_code==200,response.text
        c=TestClient(app,headers={'Origin':'http://testserver'})
        response=c.post('/api/login',json={'email':email,'password':PASSWORD})
        assert response.status_code==200,response.text
        c.headers['X-CSRF-Token']=c.get('/api/admin/session').json()['csrf']
        clients.append(c)
        return c
    yield make
    for c in clients:c.close()

def create_service(client,title='Private Idee',slug='private-idee'):
    response=client.post('/api/admin/content',json={'kind':'service','data':{'title':title,'slug':slug,'description':'Ein Testinhalt'}})
    assert response.status_code==200,response.text
    return response.json()

def action(client,row,name,**kwargs):
    response=client.post(f"/api/admin/content/{row['id']}/{name}",json={'expected_revision':row['revision'],**kwargs})
    assert response.status_code==200,response.text
    return response.json()
