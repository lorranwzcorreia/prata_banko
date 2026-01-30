"""
APP.PY - SISTEMA UNIFICADO BANCO PRATA
Versão SIMPLIFICADA e COMPATÍVEL com seus robôs
"""

import os
import sys
import threading
import queue
import time
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime

# Importar robôs
from robo_autorizacoes import RoboAutorizacoes
from robo_consultas import RoboConsultas

app = Flask(__name__)

# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, '../dados/para_autorizar')
app.config['AUTORIZADOS_FOLDER'] = os.path.join(BASE_DIR, '../dados/autorizados')
app.config['RESULTS_FOLDER'] = os.path.join(BASE_DIR, '../resultados')

# Criar pastas
for folder in [app.config['UPLOAD_FOLDER'], 
               app.config['AUTORIZADOS_FOLDER'], 
               app.config['RESULTS_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Filas e tarefas
auth_queue = queue.Queue()
consulta_queue = queue.Queue()
auth_tasks = {}
consulta_tasks = {}

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

# ========== AUTORIZAÇÕES ==========

@app.route('/autorizar/upload', methods=['POST'])
def upload_autorizar():
    """Upload para autorizações"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nome de arquivo vazio'}), 400
    
    # Salvar arquivo
    timestamp = int(time.time())
    filename = f"para_autorizar_{timestamp}.txt"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Ler clientes
    clientes = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                linha = line.strip()
                if not linha:
                    continue
                
                # Formato: CPF NOME TELEFONE
                partes = linha.split()
                if len(partes) >= 3:
                    cpf = partes[0]
                    cpf_limpo = ''.join(filter(str.isdigit, cpf))
                    
                    if len(cpf_limpo) == 11:
                        nome = ' '.join(partes[1:-1])
                        telefone = partes[-1]
                        
                        clientes.append({
                            'cpf': cpf_limpo,
                            'nome': nome,
                            'telefone': telefone
                        })
    except Exception as e:
        return jsonify({'error': f'Erro ao ler arquivo: {str(e)}'}), 500
    
    if not clientes:
        return jsonify({'error': 'Nenhum cliente válido encontrado'}), 400
    
    # Criar tarefa
    task_id = f"auth_{timestamp}"
    auth_tasks[task_id] = {
        'tipo': 'autorizacao',
        'status': 'pending',
        'total': len(clientes),
        'processados': 0,
        'autorizados': 0,
        'start_time': time.time(),
        'clientes': clientes,
        'resultados': [],
        'arquivo_saida': None
    }
    
    # Adicionar à fila
    auth_queue.put(task_id)
    
    # Iniciar worker se não estiver rodando
    if not hasattr(app, 'auth_worker_running'):
        app.auth_worker_running = True
        thread = threading.Thread(target=auth_worker_process, daemon=True)
        thread.start()
        print("👷 Worker de autorizações iniciado")
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': f'{len(clientes)} clientes para autorizar',
        'total': len(clientes)
    })

@app.route('/autorizar/status/<task_id>')
def auth_status(task_id):
    """Status da autorização"""
    if task_id not in auth_tasks:
        return jsonify({'error': 'Tarefa não encontrada'}), 404
    
    task = auth_tasks[task_id]
    
    progresso = (task['processados'] / task['total'] * 100) if task['total'] > 0 else 0
    
    return jsonify({
        'success': True,
        'status': task['status'],
        'total': task['total'],
        'processados': task['processados'],
        'autorizados': task['autorizados'],
        'progresso': round(progresso, 1),
        'tempo': round(time.time() - task['start_time'], 1),
        'arquivo_saida': task['arquivo_saida']
    })

@app.route('/autorizar/download/<task_id>')
def download_autorizados(task_id):
    """Download do arquivo de autorizados"""
    if task_id not in auth_tasks:
        return jsonify({'error': 'Tarefa não encontrada'}), 404
    
    task = auth_tasks[task_id]
    
    if not task['arquivo_saida']:
        return jsonify({'error': 'Arquivo não gerado ainda'}), 404
    
    filepath = os.path.join(app.config['AUTORIZADOS_FOLDER'], task['arquivo_saida'])
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"clientes_autorizados_{task_id}.txt",
        mimetype='text/plain'
    )

def auth_worker_process():
    """Worker de autorizações"""
    print("👷 Worker de autorizações iniciado...")
    
    while True:
        try:
            task_id = auth_queue.get(timeout=30)
            
            if task_id not in auth_tasks:
                continue
            
            task = auth_tasks[task_id]
            task['status'] = 'processing'
            
            print(f"🚀 Processando autorizações: {task_id} ({task['total']} clientes)")
            
            try:
                # Criar robô
                robo = RoboAutorizacoes()
                
                # Processar clientes
                resultados = robo.processar_lista(task['clientes'])
                
                # Salvar autorizados
                autorizados = [r for r in resultados if r['autorizado']]
                
                if autorizados:
                    filename = f"autorizados_{task_id}.txt"
                    filepath = os.path.join(app.config['AUTORIZADOS_FOLDER'], filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        for cliente in autorizados:
                            f.write(f"{cliente['cpf']}\t{cliente['nome']}\t{cliente['telefone']}\n")
                    
                    task['arquivo_saida'] = filename
                    print(f"💾 {len(autorizados)} clientes autorizados salvos")
                
                # Atualizar tarefa
                task['status'] = 'completed'
                task['resultados'] = resultados
                task['processados'] = len(resultados)
                task['autorizados'] = len(autorizados)
                
                print(f"✅ Autorizações concluídas: {task['autorizados']}/{task['total']} autorizados")
                
            except Exception as e:
                print(f"❌ Erro no processamento: {e}")
                import traceback
                traceback.print_exc()
                task['status'] = 'error'
                
        except queue.Empty:
            time.sleep(5)
        except Exception as e:
            print(f"❌ Erro no worker: {e}")
            time.sleep(10)

# ========== CONSULTAS ==========

@app.route('/consultar/upload', methods=['POST'])
def upload_consultar():
    """Upload para consultas"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nome de arquivo vazio'}), 400
    
    # Salvar arquivo
    timestamp = int(time.time())
    filename = f"para_consultar_{timestamp}.txt"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Ler clientes
    clientes = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                linha = line.strip()
                if not linha:
                    continue
                
                # Formato: CPF TAB Nome TAB Telefone
                partes = linha.split('\t')
                if len(partes) < 3:
                    partes = linha.split()
                
                if len(partes) >= 3:
                    cpf = partes[0]
                    cpf_limpo = ''.join(filter(str.isdigit, cpf))
                    
                    if len(cpf_limpo) == 11:
                        nome = ' '.join(partes[1:-1])
                        telefone = partes[-1]
                        
                        clientes.append({
                            'cpf': cpf_limpo,
                            'nome': nome,
                            'telefone': telefone
                        })
    except Exception as e:
        return jsonify({'error': f'Erro ao ler arquivo: {str(e)}'}), 500
    
    if not clientes:
        return jsonify({'error': 'Nenhum cliente válido encontrado'}), 400
    
    # Configuração
    fazer_reconsulta = request.form.get('reconsulta', 'true').lower() == 'true'
    
    # Criar tarefa
    task_id = f"cons_{timestamp}"
    consulta_tasks[task_id] = {
        'tipo': 'consulta',
        'status': 'pending',
        'total': len(clientes),
        'processados': 0,
        'start_time': time.time(),
        'clientes': clientes,
        'fazer_reconsulta': fazer_reconsulta,
        'estatisticas': {
            'total': len(clientes),
            'sucesso_fase1': 0,
            'sucesso_fase2': 0,
            'inelegiveis': 0,
            'erros': 0
        },
        'resultados': [],
        'arquivo_saida': None
    }
    
    # Adicionar à fila
    consulta_queue.put(task_id)
    
    # Iniciar worker se não estiver rodando
    if not hasattr(app, 'consulta_worker_running'):
        app.consulta_worker_running = True
        thread = threading.Thread(target=consulta_worker_process, daemon=True)
        thread.start()
        print("👷 Worker de consultas iniciado")
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': f'{len(clientes)} clientes para consulta',
        'total': len(clientes),
        'fazer_reconsulta': fazer_reconsulta
    })

@app.route('/consultar/status/<task_id>')
def consultar_status(task_id):
    """Status da consulta"""
    if task_id not in consulta_tasks:
        return jsonify({'error': 'Tarefa não encontrada'}), 404
    
    task = consulta_tasks[task_id]
    
    progresso = (task['processados'] / task['total'] * 100) if task['total'] > 0 else 0
    
    return jsonify({
        'success': True,
        'status': task['status'],
        'total': task['total'],
        'processados': task['processados'],
        'progresso': round(progresso, 1),
        'tempo': round(time.time() - task['start_time'], 1),
        'fazer_reconsulta': task['fazer_reconsulta'],
        'estatisticas': task['estatisticas'],
        'arquivo_saida': task['arquivo_saida']
    })

@app.route('/consultar/download/<task_id>')
def download_consultas(task_id):
    """Download do Excel com resultados"""
    if task_id not in consulta_tasks:
        return jsonify({'error': 'Tarefa não encontrada'}), 404
    
    task = consulta_tasks[task_id]
    
    if not task['arquivo_saida']:
        return jsonify({'error': 'Arquivo não gerado ainda'}), 404
    
    filepath = os.path.join(app.config['RESULTS_FOLDER'], task['arquivo_saida'])
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"resultados_consultas_{task_id}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def consulta_worker_process():
    """Worker de consultas - VERSÃO SIMPLIFICADA E FUNCIONAL"""
    print("👷 Worker de consultas iniciado...")
    
    while True:
        try:
            task_id = consulta_queue.get(timeout=30)
            
            if task_id not in consulta_tasks:
                continue
            
            task = consulta_tasks[task_id]
            task['status'] = 'processing'
            
            print(f"🚀 Processando consultas: {task_id} ({task['total']} clientes)")
            print(f"📋 Reconsulta: {task['fazer_reconsulta']}")
            
            try:
                # Criar robô
                robo = RoboConsultas()
                
                # SIMPLES: Usar o método processar_lista que já faz tudo
                resultados = robo.processar_lista(
                    lista_clientes=task['clientes'],
                    fazer_reconsulta=task['fazer_reconsulta']
                )
                
                # Salvar Excel
                if resultados:
                    filename = f"resultados_{task_id}.xlsx"
                    filepath = os.path.join(app.config['RESULTS_FOLDER'], filename)
                    robo.salvar_resultados_excel(resultados, filepath)
                    
                    task['arquivo_saida'] = filename
                    
                    # Calcular estatísticas
                    for resultado in resultados:
                        if resultado.get('status_fase1') == 'sucesso':
                            task['estatisticas']['sucesso_fase1'] += 1
                        elif resultado.get('status_fase1') == 'inelegivel':
                            task['estatisticas']['inelegiveis'] += 1
                        elif resultado.get('status_fase1') not in ['pendente', 'sucesso', 'inelegivel']:
                            task['estatisticas']['erros'] += 1
                        
                        if task['fazer_reconsulta'] and resultado.get('status_fase2') == 'sucesso':
                            task['estatisticas']['sucesso_fase2'] += 1
                
                # Atualizar tarefa
                task['status'] = 'completed'
                task['resultados'] = resultados
                task['processados'] = task['total']
                
                print(f"✅ Consultas concluídas: {task_id}")
                print(f"📊 Estatísticas: {task['estatisticas']}")
                
            except Exception as e:
                print(f"❌ Erro no processamento: {e}")
                import traceback
                traceback.print_exc()
                task['status'] = 'error'
                
        except queue.Empty:
            time.sleep(5)
        except Exception as e:
            print(f"❌ Erro no worker: {e}")
            time.sleep(10)

# ========== UTILITÁRIOS ==========

@app.route('/listar/autorizados')
def listar_autorizados():
    """Lista arquivos de autorizados"""
    arquivos = []
    try:
        for file in os.listdir(app.config['AUTORIZADOS_FOLDER']):
            if file.endswith('.txt'):
                filepath = os.path.join(app.config['AUTORIZADOS_FOLDER'], file)
                size = os.path.getsize(filepath)
                
                # Contar linhas
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = sum(1 for _ in f)
                
                arquivos.append({
                    'nome': file,
                    'tamanho': f"{size/1024:.1f} KB",
                    'clientes': lines
                })
    except:
        pass
    
    return jsonify({'success': True, 'arquivos': arquivos})

@app.route('/listar/tarefas')
def listar_tarefas():
    """Lista tarefas recentes"""
    auth_list = []
    consulta_list = []
    
    for task_id, task in auth_tasks.items():
        auth_list.append({
            'id': task_id,
            'status': task.get('status', 'unknown'),
            'total': task.get('total', 0),
            'autorizados': task.get('autorizados', 0),
            'tempo': round(time.time() - task.get('start_time', time.time()), 1)
        })
    
    for task_id, task in consulta_tasks.items():
        consulta_list.append({
            'id': task_id,
            'status': task.get('status', 'unknown'),
            'total': task.get('total', 0),
            'processados': task.get('processados', 0),
            'tempo': round(time.time() - task.get('start_time', time.time()), 1)
        })
    
    return jsonify({
        'success': True,
        'autorizacoes': auth_list[-5:],  # Últimas 5
        'consultas': consulta_list[-5:]   # Últimas 5
    })

# ========== INICIAR SERVIDOR ==========

if __name__ == '__main__':
    # Iniciar workers
    auth_thread = threading.Thread(target=auth_worker_process, daemon=True)
    auth_thread.start()
    
    consulta_thread = threading.Thread(target=consulta_worker_process, daemon=True)
    consulta_thread.start()
    
    print("\n" + "="*50)
    print("🚀 SISTEMA UNIFICADO BANCO PRATA")
    print("="*50)
    print("🌐 Acesse: http://localhost:5000")
    print("✨ Funcionalidades:")
    print("  🔐 Autorizações (usando seu robô)")
    print("  💰 Consultas (usando seu robô)")
    print("="*50)
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)