from flask import Flask,make_response,jsonify,request
from db_connnection import MySQLDatabase
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token,jwt_required
from datetime import timedelta
import bcrypt
import os
import json
from dotenv import load_dotenv

load_dotenv()

try:
    mydb = MySQLDatabase()
    print(f"Iniciando conexão...\nStatus: {mydb.conn.is_connected()}")
except ConnectionError as err:
    raise "Erro durante a conexão. Message:{err}"


app = Flask(__name__)

app.json.sort_keys = False
secret_key = os.getenv("JWT_SECRET_KEY")
app.config['JWT_SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://usuario:root@localhost/sistemaestagios'
db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.BigInteger, primary_key=True,nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    senha = db.Column(db.String(255), nullable=True)
    roles_id = db.Column(db.BigInteger, primary_key=False,nullable=False)


@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"msg": "Token não fornecido ou inválido."}), 401


@jwt.expired_token_loader
def expired_token_response(jwt_header, jwt_payload):
    return jsonify({"msg": "O token fornecido expirou."}), 401


@jwt.invalid_token_loader
def invalid_token_response(callback):
    return jsonify({"msg": "O token fornecido é inválido."}), 422


@app.route('/id_request/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def get_dados(EnrollStudent):

    
    cursor = mydb.conn.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE matricula = %s', [EnrollStudent])

    meus_dados = cursor.fetchall()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Não foi encontrada nenhuma requisição de estágio para a matrícula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisição de estágio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )


@app.route('/dados',methods=['POST'])
@jwt_required()
def create_dados():
    dado = request.json
    
    cursor = mydb.conn.cursor()
    sql = f"INSERT INTO dados (marca,modelo,ano) VALUES ('{dado['marca']}','{dado['modelo']}',{dado['ano']})"
    cursor.execute(sql)
    mydb.conn.commit()
    
    return make_response(
        jsonify(
            mensagem='Dado cadastrado com sucesso',
            dado=dado
        )
    )

@app.route('/delete_docs/<int:RequestId>',methods=['DELETE'])
@jwt_required()
def delete_docs(RequestId):
    
    cursor = mydb.conn.cursor()
    cursor.execute('SELECT * FROM documento WHERE solicitar_estagio_id = %s', [RequestId])
       
    meus_dados = cursor.fetchall()

    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Não foram encontrados documentos para requisição de estágio {RequestId}!",            
        )
    )
    else:
        cursor.execute('DELETE FROM documento WHERE solicitar_estagio_id = %s', [RequestId])
        mydb.conn.commit()
        return make_response(
            jsonify(                
                mensagem=f'Documentos da requisição de estágio {RequestId} excluídos com sucesso!',        
            )
        )


@app.route('/delete_history_request/<int:RequestId>',methods=['DELETE'])
@jwt_required()
def delete_history_request(RequestId):
    
    cursor = mydb.conn.cursor()    
    cursor.execute('SELECT * FROM historico_solicitacao WHERE solicitar_estagio_id = %s', [RequestId])       
    meus_dados = cursor.fetchall()

    if len(meus_dados) == 0:
        return make_response(
            jsonify(
                mensagem=f"Não foi encontrado histórico para requisição de estágio {RequestId}!",            
            )
        )
    else:
        cursor.execute('DELETE FROM historico_solicitacao WHERE solicitar_estagio_id = %s', [RequestId])
        mydb.conn.commit()
        return make_response(
            jsonify(                
                mensagem=f'Histórico da requisição de estágio {RequestId} excluído com sucesso!',        
            )
        )

@app.route('/delete_request/<int:RequestId>',methods=['DELETE'])
@jwt_required()
def delete_request(RequestId):
    
    cursor = mydb.conn.cursor()
    cursor.execute('SELECT * FROM solicitar_estagio WHERE id = %s', [RequestId])    
    meus_dados = cursor.fetchall()

    if len(meus_dados) == 0:
        return make_response(
            jsonify(
                mensagem=f"Não foi encontrada requisição de estágio ID {RequestId}!",            
            )
        )
    else:
        cursor.execute('DELETE FROM solicitar_estagio WHERE id = %s', [RequestId])
        mydb.conn.commit()
        return make_response(
            jsonify(                
                mensagem=f'Requisição de estágio {RequestId} excluída com sucesso!',        
            )
        )

@app.route('/delete_interns/<int:RequestId>',methods=['DELETE'])
@jwt_required()
def delete_interns(RequestId):
    
    cursor = mydb.conn.cursor()
    cursor.execute('SELECT * FROM estagiarios WHERE solicitacao_id = %s', [RequestId])    
    meus_dados = cursor.fetchall()
    
    if len(meus_dados) == 0:
        return make_response(
            jsonify(
                mensagem=f"Não foi encontrado estagiário para requisição de estágio ID {RequestId}!",            
            )
        )
    else:
        cursor.execute('DELETE FROM estagiarios WHERE solicitacao_id = %s', [RequestId])
        mydb.conn.commit()
        return make_response(
            jsonify(                
                mensagem=f'Registro excluído da tabela estagiários!',        
            )
        )
        

@app.route('/auth', methods=['POST'])
def login():
    print(type('email'))
    username = request.json.get('email')
    password = request.json.get('senha').encode('utf-8')
    user = User.query.filter_by(email=username).first()
    user_senha = user.senha.encode('utf-8')   
    if user and bcrypt.checkpw(password,user_senha):
        print  ("Login com sucesso")
        access_token = create_access_token(identity=username,expires_delta=timedelta(minutes=10))
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Usuário ou senha inválidos"}), 401


app.run()

