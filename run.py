#!/usr/bin/env python3
"""
Script para iniciar o Sistema Unificado Banco Prata
"""

import os
import sys
import subprocess

def main():
    print("\n" + "="*60)
    print("🏦 SISTEMA UNIFICADO BANCO PRATA - INSTALADOR")
    print("="*60)
    
    # Verificar estrutura
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 Diretório base: {base_dir}")
    
    # Verificar pastas necessárias
    pastas = [
        '../autorizacoes',
        '../consultas', 
        '../dados',
        '../resultados'
    ]
    
    print("\n🔍 Verificando estrutura de pastas...")
    for pasta in pastas:
        caminho = os.path.join(base_dir, pasta)
        if os.path.exists(caminho):
            print(f"   ✅ {pasta}")
        else:
            print(f"   ❌ {pasta} (não encontrada)")
            criar = input(f"    Criar pasta {pasta}? (s/n): ")
            if criar.lower() == 's':
                os.makedirs(caminho, exist_ok=True)
                print(f"    ✅ Pasta criada: {caminho}")
    
    # Verificar dependências
    print("\n📦 Verificando dependências...")
    try:
        import flask
        print("   ✅ Flask")
    except:
        print("   ❌ Flask não instalado")
        instalar = input("    Instalar Flask? (s/n): ")
        if instalar.lower() == 's':
            subprocess.run([sys.executable, "-m", "pip", "install", "flask"])
    
    try:
        import selenium
        print("   ✅ Selenium")
    except:
        print("   ❌ Selenium não instalado")
        instalar = input("    Instalar Selenium? (s/n): ")
        if instalar.lower() == 's':
            subprocess.run([sys.executable, "-m", "pip", "install", "selenium"])
    
    try:
        import pandas
        print("   ✅ Pandas")
    except:
        print("   ❌ Pandas não instalado")
        instalar = input("    Instalar Pandas? (s/n): ")
        if instalar.lower() == 's':
            subprocess.run([sys.executable, "-m", "pip", "install", "pandas"])
    
    # Verificar ChromeDriver
    print("\n🌐 Verificando ChromeDriver...")
    try:
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("   ✅ ChromeDriver funcionando")
    except Exception as e:
        print(f"   ❌ ChromeDriver erro: {e}")
        print("\n⚠️  Instale o ChromeDriver:")
        print("   1. Baixe: https://chromedriver.chromium.org/")
        print("   2. Extraia e coloque no PATH do sistema")
        print("   3. Ou coloque na pasta do sistema")
    
    # Verificar arquivos dos robôs nas pastas existentes
    print("\n🤖 Verificando robôs existentes...")
    robos_necessarios = [
        ('../autorizacoes/robo_autorizacoes.py', 'Robô de Autorizações'),
        ('../consultas/robo_consultas.py', 'Robô de Consultas')
    ]
    
    for arquivo, nome in robos_necessarios:
        caminho = os.path.join(base_dir, arquivo)
        if os.path.exists(caminho):
            print(f"   ✅ {nome} encontrado")
        else:
            print(f"   ❌ {nome} não encontrado")
            print(f"    Caminho esperado: {caminho}")
            print(f"    ⚠️  Você precisa dos arquivos originais nas pastas autorizacoes/ e consultas/")
    
    # Iniciar sistema
    print("\n" + "="*60)
    print("🚀 INICIANDO SISTEMA UNIFICADO")
    print("="*60)
    
    input("\nPressione Enter para iniciar o sistema na porta 5000...")
    
    # Importar e executar o app
    sys.path.insert(0, base_dir)
    
    try:
        from app import app
        print("\n✅ Sistema importado com sucesso!")
        print(f"🌐 Acesse: http://localhost:5000")
        print("\n🛑 Para parar o sistema, pressione Ctrl+C")
        print("="*60)
        
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except Exception as e:
        print(f"\n❌ Erro ao iniciar sistema: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")

if __name__ == '__main__':
    main()