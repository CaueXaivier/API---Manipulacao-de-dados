from flask import Flask,make_response,jsonify,request
from db_connnection import MySQLDatabase
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token,jwt_required
from datetime import timedelta
import bcrypt
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()


app = Flask(__name__)

app.json.sort_keys = False
secret_key = os.getenv("JWT_SECRET_KEY")
app.config['JWT_SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
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


def get_db_connection():
    return mysql.connector.connect(
        host = os.getenv("HOST"),
        user = os.getenv("USERNAME"),
        database = os.getenv("DATABASE")
    )

@app.route('/id_request/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def get_dados(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (1,2,3,4) and  tipo = "Obrigatório" and matricula = %s', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )


@app.route('/delete_docs/<int:RequestId>',methods=['DELETE'])
@jwt_required()
def delete_docs(RequestId):
    
    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT * FROM documento WHERE solicitar_estagio_id = %s', [RequestId])       
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foram encontrados documentos para requisicao de estagio {RequestId}!",            
        )
    )
    else:
        cursor.execute('DELETE FROM documento WHERE solicitar_estagio_id = %s', [RequestId])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Documentos da requisicao de estagio {RequestId} excluidos com sucesso!',        
            )
        )


@app.route('/delete_history_request/<int:RequestId>',methods=['DELETE'])
@jwt_required()
def delete_history_request(RequestId):
 
    mydb = get_db_connection()
    cursor = mydb.cursor()   
    cursor.execute('SELECT * FROM historico_solicitacao WHERE solicitar_estagio_id = %s', [RequestId])       
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
            jsonify(
                mensagem=f"Nao foi encontrado historico para requisicao de estagio {RequestId}!",            
            )
        )
    else:
        cursor.execute('DELETE FROM historico_solicitacao WHERE solicitar_estagio_id = %s', [RequestId])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Historico da requisicao de estagio {RequestId} excluido com sucesso!',        
            )
        )

@app.route('/delete_request/<int:RequestId>',methods=['DELETE'])
@jwt_required()
def delete_request(RequestId):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT * FROM solicitar_estagio WHERE id = %s', [RequestId])    
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
            jsonify(
                mensagem=f"Nao foi encontrada requisição de estagio ID {RequestId}!",            
            )
        )
    else:
        cursor.execute('DELETE FROM solicitar_estagio WHERE id = %s', [RequestId])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Requisicao de estagio {RequestId} excluida com sucesso!',        
            )
        )

@app.route('/delete_interns/<int:RequestId>',methods=['DELETE'])
@jwt_required()
def delete_interns(RequestId):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT * FROM estagiarios WHERE solicitacao_id = %s', [RequestId])    
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
            jsonify(
                mensagem=f"Nao foi encontrado estagiario para requisicao de estagio ID {RequestId}!",            
            )
        )
    else:
        cursor.execute('DELETE FROM estagiarios WHERE solicitacao_id = %s', [RequestId])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Registro excluido da tabela estagiarios!',        
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
        access_token = create_access_token(identity=username,expires_delta=timedelta(minutes=30))
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Usuario ou senha invalidos"}), 401


@app.route('/delete_server/<string:EmailServer>',methods=['DELETE'])
@jwt_required()
def delete_server(EmailServer):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT * FROM usuarios WHERE email = %s', [EmailServer])    
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
            jsonify(
                mensagem=f"Nao foi encontrado servidor com e-mail: {EmailServer}!",            
            )
        )
    else:
        cursor.execute('DELETE S FROM servidores S INNER JOIN usuarios U ON S.usuario_sistema_id = U.id WHERE U.email = %s', [EmailServer])
        mydb.commit()
        cursor.execute('DELETE FROM usuarios WHERE email = %s', [EmailServer])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Registro excluido da tabela usuarios!',        
            )
        )
    
@app.route('/id_course_active/<string:NameCourse>',methods=['GET'])
@jwt_required()
def id_course_active(NameCourse):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM curso WHERE ativo = 1 and  nome_curso = %s', [NameCourse])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada curso ativo com nome {NameCourse}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID do curso':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/id_course_inactive/<string:NameCourse>',methods=['GET'])
@jwt_required()
def id_course_inactive(NameCourse):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM curso WHERE ativo = 0 and  nome_curso = %s', [NameCourse])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada curso inativo com nome {NameCourse}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID do curso':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/active_course/<int:IdCourse>',methods=['PUT'])
@jwt_required()
def active_course(IdCourse):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM curso WHERE ativo = 0 and  id = %s', [IdCourse])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada curso inativo com ID {IdCourse}!",            
        )
    )
    else:
        cursor.execute('UPDATE curso SET ativo = 1 WHERE  id = %s', [IdCourse])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Alterado status do curso para ativo!',        
            )
        )
    
@app.route('/insert_course',methods=['POST'])
def insert_course():
    dado = request.json  
    mydb = get_db_connection()
    cursor = mydb.cursor()   
    sql = f"INSERT INTO curso (ativo,nome_curso) VALUES ('{dado['status']}','{dado['nome']}')"
    cursor.execute(sql)
    mydb.commit()
    return make_response(
        jsonify(
            mensagem='Curso cadastrado com sucesso!',
        )
    )

@app.route('/inactive_course/<int:IdCourse>',methods=['PUT'])
@jwt_required()
def inactive_course(IdCourse):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM curso WHERE ativo = 1 and  id = %s', [IdCourse])
    meus_dados = cursor.fetchall()  
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada curso ativo com ID {IdCourse}!",            
        )
    )
    else:
        cursor.execute('UPDATE curso SET ativo = 0 WHERE  id = %s', [IdCourse])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Alterado status do curso para inativo!',        
            )
        )

@app.route('/insert_request',methods=['POST'])
def insert_request():
    dado = request.json    
    mydb = get_db_connection()
    cursor = mydb.cursor()  
    sql = f"INSERT INTO solicitar_estagio (agente,cancelamento,carga_horaria,contato_empresa,data_solicitacao,e_privada,editavel,etapa,final_data_estagio,inicio_data_estagio,nome_empresa,observacao,relatorio_entregue,resposta,salario,status,status_etapa_coordenador,status_etapa_diretor,status_setor_estagio,tipo,turno_estagio,aluno_id,curso_id)  VALUES ('{dado['agente']}',{dado['cancelamento']},'{dado['carga_horaria']}','{dado['contato_empresa']}','{dado['data_solicitacao']}','{dado['e_privada']}',{dado['editavel']},'{dado['etapa']}','{dado['final_data_estagio']}','{dado['inicio_data_estagio']}','{dado['nome_empresa']}','{dado['observacao']}',{dado['relatorio_entregue']},'{dado['resposta']}','{dado['salario']}','{dado['status']}','{dado['status_etapa_coordenador']}','{dado['status_etapa_diretor']}','{dado['status_setor_estagio']}','{dado['tipo']}','{dado['turno_estagio']}','{dado['aluno_id']}','{dado['curso_id']}')"
    cursor.execute(sql)
    mydb.commit()
    return make_response(
        jsonify(
            mensagem='Solicitacao de estagio cadastrada com sucesso!',
        )
    )

@app.route('/id_server/<string:EmailServer>',methods=['GET'])
@jwt_required()
def id_server(EmailServer):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM usuarios WHERE roles_id= 3 and  email = %s', [EmailServer])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrado servidor com e-mail {EmailServer}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID do servidor':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )


@app.route('/insert_server_user',methods=['POST'])
def insert_server_user():
    dado = request.json  
    mydb = get_db_connection()
    cursor = mydb.cursor()   
    sql = f"INSERT INTO usuarios (email,senha,roles_id) VALUES ('{dado['email']}','{dado['senha']}','{dado['roles_id']}')"
    cursor.execute(sql)
    mydb.commit()
    return make_response(
        jsonify(
            mensagem='Servidor cadastrado com sucesso na tabela usuarios!',
        )
    )

@app.route('/insert_server',methods=['POST'])
def insert_server():
    dado = request.json  
    mydb = get_db_connection()
    cursor = mydb.cursor()   
    print (dado)
    sql = f"INSERT INTO servidores (cargo,nome,curso_id,role_id,usuario_sistema_id) VALUES ('{dado['cargo']}','{dado['nome']}','{dado['curso_id']}','{dado['role_id']}','{dado['usuario_sistema_id']}')"
    cursor.execute(sql)
    mydb.commit()
    return make_response(
        jsonify(
            mensagem='Servidor cadastrado com sucesso!',
        )
    )

@app.route('/id_student/<string:EmailStudent>',methods=['GET'])
@jwt_required()
def id_student(EmailStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM usuarios WHERE roles_id= 1 and  email = %s', [EmailStudent])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrado aluno com e-mail {EmailStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID do aluno':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/insert_student_user',methods=['POST'])
def insert_student_user():
    dado = request.json  
    mydb = get_db_connection()
    cursor = mydb.cursor()   
    sql = f"INSERT INTO usuarios (email,senha,roles_id) VALUES ('{dado['email']}','{dado['senha']}','{dado['roles_id']}')"
    cursor.execute(sql)
    mydb.commit()
    return make_response(
        jsonify(
            mensagem='Aluno cadastrado com sucesso na tabela usuarios!',
        )
    )

@app.route('/insert_student',methods=['POST'])
def insert_student():
    dado = request.json  
    mydb = get_db_connection()
    cursor = mydb.cursor()   
    print (dado)
    sql = f"INSERT INTO aluno (matricula,nome_completo,turno,curso_id,role_id,usuario_sistema_id) VALUES ('{dado['matricula']}','{dado['nome_completo']}','{dado['turno']}','{dado['curso_id']}','{dado['role_id']}','{dado['usuario_sistema_id']}')"
    cursor.execute(sql)
    mydb.commit()
    return make_response(
        jsonify(
            mensagem='Aluno cadastrado com sucesso!',
        )
    )

@app.route('/id_request_approved/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_approved(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (5) and relatorio_entregue = 1 and  tipo = "Obrigatório" and matricula = %s', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio finalizada para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/update_request_approved/<int:IdRequest>',methods=['PUT'])
@jwt_required()
def update_request_approved(IdRequest):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM solicitar_estagio WHERE id = %s', [IdRequest])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada requisicao de estagio com ID {IdRequest}!",            
        )
    )
    else:
        cursor.execute("UPDATE solicitar_estagio SET etapa = 3,status = 'Em análise' WHERE  id = %s", [IdRequest])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Alterado status da requisicao para Em analise!',        
            )
        )

@app.route('/id_request_finished/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_finished(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute("SELECT  SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa = 5 and status = 'Finalizado' and relatorio_entregue = 1 and tipo = 'Obrigatório' and matricula = %s  LIMIT 1", [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )
    
@app.route('/id_request_renewal_coordinator/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_renewal_coordinator(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (1,2,4,5) and tipo = "Renovação" and matricula = %s', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )
@app.route('/update_request_renewal_coordinator/<int:IdRequest>',methods=['PUT'])
@jwt_required()
def update_request_renewal_coordinator(IdRequest):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM solicitar_estagio WHERE id = %s', [IdRequest])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada requisicao de estagio com ID {IdRequest}!",            
        )
    )
    else:
        cursor.execute("UPDATE solicitar_estagio SET etapa = 3,status = 'Em análise' WHERE  id = %s", [IdRequest])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Alterado status da requisicao para Em analise!',        
            )
        )
    
@app.route('/id_request_renewal_approved/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_renewal_approved(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute("SELECT  SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa = 5 and status = 'Aprovado' and tipo = 'Renovação' and matricula = %s  LIMIT 1", [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/id_request_approved_no_report_delivered/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_approved_no_report_delivered(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (5) and relatorio_entregue = 0 and  tipo = "Obrigatório" and cancelamento = 0 and status = "Aprovado" and matricula = %s  LIMIT 1', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio aprovada para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )
    
@app.route('/update_request_cancellation_coordinator/<int:IdRequest>',methods=['PUT'])
@jwt_required()
def update_request_cancellation_coordinator(IdRequest):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM solicitar_estagio WHERE id = %s', [IdRequest])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada requisicao de estagio com ID {IdRequest}!",            
        )
    )
    else:
        cursor.execute("UPDATE solicitar_estagio SET etapa = 3,status = 'Em análise',cancelamento = 1 WHERE  id = %s", [IdRequest])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Alterado status da requisicao para Em analise!',        
            )
        )


@app.route('/id_request_cancelled/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_cancelled(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (2) and relatorio_entregue = 0 and  tipo = "Obrigatório" and cancelamento = 1 and status = "Em análise" and matricula = %s  LIMIT 1', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio cancelada para matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/id_request_credit/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_credit(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (3) and relatorio_entregue = 0 and  tipo = "Aproveitamento APRO4" and cancelamento = 0 and status = "Em análise" and matricula = %s  LIMIT 1', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de aproveitamento para matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de aproveitamento':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/id_request_credit_approved/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_credit_approved(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (5) and relatorio_entregue = 0 and  tipo = "Aproveitamento APRO4" and cancelamento = 0 and status = "Aprovado" and matricula = %s  LIMIT 1', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de aproveitamento aprovada para matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de aproveitamento':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/id_request_approved_not_report/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_approved_not_report(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (5) and relatorio_entregue = 0 and  tipo = "Obrigatório" and matricula = %s', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio aprovada para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )
    
@app.route('/update_request_cancellation_director/<int:IdRequest>',methods=['PUT'])
@jwt_required()
def update_request_cancellation_director(IdRequest):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM solicitar_estagio WHERE id = %s', [IdRequest])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada requisicao de estagio com ID {IdRequest}!",            
        )
    )
    else:
        cursor.execute("UPDATE solicitar_estagio SET etapa = 4,status = 'Em análise',cancelamento = 1 WHERE  id = %s", [IdRequest])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Alterado status da requisicao para Em analise!',        
            )
        )

@app.route('/id_request_renewal_director/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_renewal_director(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (1,2,3,5) and tipo = "Renovação" and matricula = %s', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/update_request_renewal_director/<int:IdRequest>',methods=['PUT'])
@jwt_required()
def update_request_renewal_director(IdRequest):

    mydb = get_db_connection()
    cursor = mydb.cursor()  
    cursor.execute('SELECT id FROM solicitar_estagio WHERE id = %s', [IdRequest])
    meus_dados = cursor.fetchall()
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada requisicao de estagio com ID {IdRequest}!",            
        )
    )
    else:
        cursor.execute("UPDATE solicitar_estagio SET etapa = 4,status = 'Em análise' WHERE  id = %s", [IdRequest])
        mydb.commit()
        return make_response(
            jsonify(                
                mensagem=f'Alterado status da requisicao para Em analise!',        
            )
        )

@app.route('/id_request_not_mandatory_approved/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_not_mandatory_approved(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (5) and cancelamento = 0 and relatorio_entregue = 0 and  tipo = "Não obrigatório" and matricula = %s', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio aprovada para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )

@app.route('/id_request_not_mandatory_analysis_director/<int:EnrollStudent>',methods=['GET'])
@jwt_required()
def id_request_not_mandatory_analysis_director(EnrollStudent):

    mydb = get_db_connection()
    cursor = mydb.cursor()
    cursor.execute('SELECT SE.id FROM solicitar_estagio SE INNER JOIN aluno AL ON SE.aluno_id = AL.id WHERE etapa in (4) and relatorio_entregue = 0 and cancelamento = 0 and  tipo = "Não obrigatório" and matricula = %s', [EnrollStudent])
    meus_dados = cursor.fetchall()
    cursor.close() 
    mydb.close()
    
    if len(meus_dados) == 0:
        return make_response(
        jsonify(
            mensagem=f"Nao foi encontrada nenhuma requisicao de estagio em análise para a matricula {EnrollStudent}!",            
        )
    )
    else:
        dados = list()
        for dado in meus_dados:
         dados.append(
            {
                'ID da requisicao de estagio':dado[0],      
            }
        )
        return make_response(
            jsonify(
                dados            
            )
        )   



app.run()

