# -*- coding: utf-8 -*-
from peewee import *

db = SqliteDatabase('/database/database.db')

class BaseModel(Model):
    class Meta:
        database = db

class Persona(BaseModel):
    name = CharField(unique=True)
    location = CharField()
    email = CharField()
    password = CharField()
    birthday = DateTimeField()
    gender = CharField()
    phone = CharField(null=True)
    political_wing = CharField()
    source_ip = CharField()
    session_time = IntegerField()


class Event(BaseModel):
    persona = IntegerField(null=True)
    time = DateTimeField()
    content_id = TextField()
    ad_id = TextField(null=True)
    event_type = TextField()
    content_data = CharField(null=True)
    ad_data = CharField(null=True)

def init_personas():
    from requests import get
    from pandas.compat import StringIO
    import pandas as pd

    # Recupera CSV com as personas
    csv = get('https://docs.google.com/spreadsheets/d/e/2PACX-1vT_IyvV0AHgk8dO9VPAoB7URU1EP2r3zYYBnM8UShVvIuo5qrG0ZNuAm-rZUwIYaxKt0aKDPATzLisZ/pub?gid=0&single=true&output=csv').text
    df_personas = pd.read_table(StringIO(csv), sep=",")
    
    # Apaga tabela Persona atual e cria nova
    Persona.drop_table()
    Persona.create_table()
    
    # Cria tabela Personas atualizada
    for _,row in df_personas.iterrows():
        Persona.insert({
                Persona.name:row['name'],
                Persona.location:row['location'],
                Persona.email:row['email'],
                Persona.password:row['password'],
                Persona.birthday:row['birthday'],
                Persona.gender:row['gender'],
                Persona.phone:row['phone'],
                Persona.political_wing:row['political_wing'],
                Persona.source_ip:row['source_ip'],
                Persona.session_time:row['session_time']}).execute()
    
    
def create_db():
    # Inicializa tabela Persona
    init_personas()
    # Inicializa tabela Event
    try:
        Event.create_table()
    except:
        print ('Tabela Event ja existe!')
