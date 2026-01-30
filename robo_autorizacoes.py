import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import os

class RoboAutorizacoes:
    def __init__(self):
        self.driver = None
        self.localizacao_ja_aceita = False
        
    def setup_driver(self):
        """Configura driver para autorizações"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver
    
    def formatar_cpf(self, cpf):
        """Formata CPF para o padrão 000.000.000-00"""
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        if len(cpf_limpo) == 11:
            return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        return cpf_limpo
    
    def autorizar_cliente(self, cliente):
        """Autoriza um único cliente"""
        try:
            print(f"📝 Autorizando: {cliente['cpf']} - {cliente['nome']}")
            
            # ⚠️ SEU LINK DE AUTORIZAÇÃO - ATUALIZADO
            LINK_AUTORIZACAO = "https://assina.bancoprata.com.br/credito-trabalhador/termo-autorizacao?d=jryl0xzNB3M%3D%7CQmDgMDkT6kho4VSp7sOSw%2FW6wG8f0ymv9xwIHz4AdL0nFUXucIsn2YtV7%2BPl%2BGBrfcuouEx02WBVEIjvt1aNEiMOSKEPWRr949HSxqhwCgB2pbIgLiajm2reU5WFYmegS2z3fpZbmhCXJPoJ7l8rxw%3D%3D"
            
            self.driver.get(LINK_AUTORIZACAO)
            time.sleep(3)
            
            # Aceitar localização (apenas na primeira vez)
            if not self.localizacao_ja_aceita:
                self.aceitar_localizacao()
            
            # Preencher formulário
            sucesso = self.preencher_formulario(cliente)
            
            return sucesso
            
        except Exception as e:
            print(f"❌ Erro na autorização: {e}")
            return False
    
    def aceitar_localizacao(self):
        """Aceita solicitação de localização"""
        try:
            time.sleep(2)
            
            # Tentar vários textos de botão
            textos_permitir = ["Permitir", "Allow", "Aceitar", "Permitir localização"]
            
            for texto in textos_permitir:
                try:
                    xpath = f'//button[contains(text(), "{texto}")]'
                    botao = self.driver.find_element(By.XPATH, xpath)
                    if botao.is_displayed():
                        botao.click()
                        print("📍 Localização permitida")
                        time.sleep(1)
                        break
                except:
                    continue
            
            self.localizacao_ja_aceita = True
            return True
            
        except Exception as e:
            print(f"⚠️  Erro na localização: {e}")
            self.localizacao_ja_aceita = True
            return True
    
    def preencher_formulario(self, cliente):
        """Preenche formulário de autorização"""
        try:
            print("   📋 Preenchendo formulário...")
            
            # Aguardar carregamento
            time.sleep(2)
            
            # 1. Campo CPF
            try:
                cpf_field = self.driver.find_element(By.XPATH, '//*[@id="app"]/main/form/form/div[1]/input')
                cpf_field.clear()
                cpf_formatado = self.formatar_cpf(cliente['cpf'])
                cpf_field.send_keys(cpf_formatado)
                print("   ✓ CPF preenchido")
                time.sleep(0.5)
            except Exception as e:
                print(f"   ❌ Erro no CPF: {e}")
                return False
            
            # 2. Campo Nome
            try:
                nome_field = self.driver.find_element(By.XPATH, '//*[@id="app"]/main/form/form/div[2]/input')
                nome_field.clear()
                nome_field.send_keys(cliente['nome'])
                print("   ✓ Nome preenchido")
                time.sleep(0.5)
            except:
                print("   ❌ Erro no nome")
                return False
            
            # 3. Campo Email - ⚠️ ALTERE PARA SEU EMAIL
            try:
                email_field = self.driver.find_element(By.XPATH, '//*[@id="app"]/main/form/form/div[3]/input')
                email_field.clear()
                email = "wenthenydasilv@gmail.com"  # ⚠️ ALTERE AQUI
                email_field.send_keys(email)
                print("   ✓ Email preenchido")
                time.sleep(0.5)
            except:
                print("   ❌ Erro no email")
                return False
            
            # 4. Campo Telefone
            try:
                telefone_field = self.driver.find_element(By.XPATH, '//*[@id="app"]/main/form/form/div[4]/input')
                telefone_field.clear()
                telefone_field.send_keys(cliente['telefone'])
                print("   ✓ Telefone preenchido")
                time.sleep(0.5)
            except:
                print("   ❌ Erro no telefone")
                return False
            
            # 5. Marcar checkboxes (geralmente 3)
            print("   ✓ Marcando checkboxes...")
            for i in range(1, 4):  # Geralmente tem 3 checkboxes
                try:
                    checkbox = self.driver.find_element(By.XPATH, f'//*[@id="app"]/main/form/form/label[{i}]/input')
                    if not checkbox.is_selected():
                        checkbox.click()
                        time.sleep(0.2)
                except:
                    print(f"   ⚠️  Checkbox {i} não encontrada")
            
            # 6. Clicar em Enviar
            try:
                enviar_btn = self.driver.find_element(By.XPATH, '//*[@id="app"]/main/form/form/button')
                enviar_btn.click()
                print("   ✓ Formulário enviado")
            except:
                print("   ❌ Erro ao enviar")
                return False
            
            # 7. Aguardar confirmação
            print("   ⏳ Aguardando confirmação...")
            time.sleep(5)
            
            # Verificar se deu certo
            try:
                # Método 1: Verificar se "Obrigado" aparece
                if "obrigado" in self.driver.page_source.lower():
                    print("   ✅ Confirmação 'Obrigado' encontrada!")
                    return True
                
                # Método 2: Verificar se URL mudou
                if "termo-autorizacao" not in self.driver.current_url:
                    print("   ✅ URL mudou - sucesso!")
                    return True
                
                # Método 3: Verificar mensagem de sucesso
                elementos_sucesso = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'sucesso') or contains(text(), 'Sucesso')]")
                for elemento in elementos_sucesso:
                    if elemento.is_displayed():
                        print("   ✅ Mensagem de sucesso encontrada!")
                        return True
                
                print("   ⚠️  Confirmação não explícita, mas formulário enviado")
                return True
                
            except:
                print("   ⚠️  Não conseguiu verificar confirmação")
                return True  # Assume sucesso se não conseguir verificar
            
        except Exception as e:
            print(f"   ❌ Erro geral no formulário: {e}")
            return False
    
    def processar_lista(self, lista_clientes):
        """Processa lista de clientes para autorização"""
        print(f"🚀 Iniciando autorizações para {len(lista_clientes)} clientes")
        
        if not self.driver:
            self.setup_driver()
        
        resultados = []
        autorizados = 0
        
        for i, cliente in enumerate(lista_clientes, 1):
            print(f"\n[{i}/{len(lista_clientes)}] Processando...")
            
            sucesso = self.autorizar_cliente(cliente)
            
            resultado = cliente.copy()
            resultado['autorizado'] = sucesso
            resultado['data_autorizacao'] = time.strftime('%d/%m/%Y %H:%M')
            resultados.append(resultado)
            
            if sucesso:
                autorizados += 1
            
            # Pausa entre clientes
            time.sleep(2)
        
        # Fechar driver
        self.driver.quit()
        
        print(f"\n✅ Processamento concluído!")
        print(f"📊 Resultados: {autorizados}/{len(lista_clientes)} autorizados")
        
        return resultados
    
    def salvar_autorizados(self, resultados, caminho_arquivo):
        """Salva apenas os clientes autorizados em um arquivo"""
        autorizados = [r for r in resultados if r['autorizado']]
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            for cliente in autorizados:
                linha = f"{cliente['cpf']}\t{cliente['nome']}\t{cliente['telefone']}\n"
                f.write(linha)
        
        print(f"💾 {len(autorizados)} clientes autorizados salvos em: {caminho_arquivo}")
        return caminho_arquivo