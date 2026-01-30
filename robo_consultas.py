"""
ROBO DE CONSULTAS - BANCO PRATA
Versão com REDUÇÃO DE 1 CENTAVO NA PARCELA para erro específico
"""

import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

class RoboConsultas:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Configura driver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        return self.driver
    
    def formatar_cpf(self, cpf):
        """Formata CPF"""
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        if len(cpf_limpo) == 11:
            return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        return cpf_limpo
    
    def login_admin(self):
        """Faz login no admin"""
        try:
            print("🔑 Fazendo login no admin...")
            
            self.driver.get("https://admin.bancoprata.com.br/")
            time.sleep(3)
            
            # Email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/span/form/span[1]/div/span/input'))
            )
            email_field.clear()
            email_field.send_keys("julia.nunes.21@gmail.com")  # ⚠️ SEU EMAIL
            time.sleep(0.5)
            
            # Senha
            senha_field = self.driver.find_element(By.XPATH, '//*[@id="content"]/span/form/span[2]/div/span/input')
            senha_field.clear()
            senha_field.send_keys("Inove@40!")  # ⚠️ SUA SENHA
            time.sleep(0.5)
            
            # Login
            login_btn = self.driver.find_element(By.XPATH, '//*[@id="content"]/span/form/div/div/button')
            login_btn.click()
            time.sleep(3)
            
            print("✅ Login realizado!")
            return True
            
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            return False
    
    def acessar_simulacao(self):
        """Acessa área de simulação"""
        try:
            print("📊 Acessando simulação...")
            
            simulacao_menu = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/section/div/nav/ul/li[4]/ul/li[1]/a'))
            )
            simulacao_menu.click()
            time.sleep(3)
            
            print("✅ Área de simulação acessada")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao acessar simulação: {e}")
            return False
    
    def verificar_erro_valor_maior_disponivel(self):
        """Verifica se apareceu o erro 'O valor desejado é maior que o disponível'"""
        try:
            # Procurar por mensagem de erro EXATA
            elementos_erro = self.driver.find_elements(By.XPATH,
                "//*[contains(translate(text(), 'O VALOR DESEJADO É MAIOR QUE O DISPONÍVEL', 'o valor desejado é maior que o disponível'), 'o valor desejado é maior que o disponível') or "
                "contains(translate(text(), 'VALOR MAIOR QUE DISPONÍVEL', 'valor maior que disponível'), 'valor maior que disponível') or "
                "contains(translate(text(), 'VALOR DESEJADO É MAIOR', 'valor desejado é maior'), 'valor desejado é maior')]"
            )
            
            for elemento in elementos_erro:
                if elemento.is_displayed():
                    texto = elemento.text.strip()
                    print(f"⚠️  ERRO ENCONTRADO: '{texto}'")
                    return True
            
            # Também verificar no source da página
            page_source = self.driver.page_source.lower()
            if "valor desejado é maior que o disponível" in page_source:
                print(f"⚠️  ERRO no page_source")
                return True
            
            return False
            
        except:
            return False
    
    def ajustar_parcela_1_centavo(self, valor_parcela_atual):
        """Ajusta valor da PARCELA subtraindo 1 centavo"""
        try:
            print(f"💰 AJUSTANDO PARCELA - 1 CENTAVO")
            print(f"   Parcela atual: {valor_parcela_atual}")
            
            # Função interna para converter valor brasileiro para numérico
            def converter_para_float(valor_br):
                # Remove R$ e espaços
                valor_limpo = re.sub(r'[^\d,]', '', valor_br)
                
                if ',' in valor_limpo:
                    # Formato brasileiro: 1.234,56
                    parte_inteira = valor_limpo.split(',')[0].replace('.', '')
                    parte_decimal = valor_limpo.split(',')[1]
                    return float(f"{parte_inteira}.{parte_decimal}")
                else:
                    # Se não tem vírgula, tratar como inteiro
                    return float(valor_limpo)
            
            # Função interna para formatar de volta
            def formatar_para_br(valor_num):
                if valor_num >= 1000:
                    return f"R$ {valor_num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    return f"R$ {valor_num:,.2f}".replace('.', ',')
            
            # Converter valor atual para numérico
            valor_numerico = converter_para_float(valor_parcela_atual)
            
            # Subtrair 0.01 (1 centavo)
            novo_valor_numerico = valor_numerico - 0.01
            
            # Arredondar para 2 casas decimais
            novo_valor_numerico = round(novo_valor_numerico, 2)
            
            # Formatar de volta
            novo_valor_formatado = formatar_para_br(novo_valor_numerico)
            
            print(f"   Nova parcela: {novo_valor_formatado}")
            return novo_valor_formatado, novo_valor_numerico
                
        except Exception as e:
            print(f"❌ Erro ao ajustar parcela: {e}")
            return valor_parcela_atual, 0
    
    def selecionar_parcelas(self):
        """Seleciona o maior número de parcelas"""
        try:
            time.sleep(1.5)
            
            # Encontrar dropdown
            try:
                xpath_dropdown = '//*[@id="app"]/section/main/div[2]/div/div[1]/span/form/div/span[2]/div/div/select'
                dropdown = self.driver.find_element(By.XPATH, xpath_dropdown)
            except:
                return 0
            
            # Usar Select
            select = Select(dropdown)
            options = select.options
            
            if len(options) <= 1:
                return 0
            
            max_parcelas = 0
            max_value = None
            
            for opcao in options:
                valor = opcao.get_attribute('value')
                texto = opcao.text.strip()
                
                if valor and texto and texto.lower() not in ['selecione uma opção', 'selecione']:
                    numeros = re.findall(r'\d+', texto)
                    if numeros:
                        num = int(numeros[0])
                        if num > max_parcelas:
                            max_parcelas = num
                            max_value = valor
            
            if max_value:
                select.select_by_value(max_value)
                print(f"✅ Selecionado {max_parcelas} parcelas")
                return max_parcelas
            
            return 0
            
        except Exception as e:
            print(f"❌ Erro ao selecionar parcelas: {e}")
            return 0
    
    def clicar_simular(self):
        """Clica no botão Simular"""
        try:
            xpath_simular = '//*[@id="app"]/section/main/div[2]/div/div[1]/span/form/div/button'
            simular_btn = self.driver.find_element(By.XPATH, xpath_simular)
            
            texto = simular_btn.text.strip()
            if "simular" in texto.lower():
                simular_btn.click()
                print("✅ Botão Simular clicado")
                return True
            return False
            
        except:
            return False
    
    def ajustar_campo_valor_parcela_manual(self, novo_valor_numerico):
        """Ajusta manualmente o campo de valor da parcela"""
        try:
            print(f"🔧 Ajustando campo manualmente para: R$ {novo_valor_numerico:.2f}")
            
            # Tentar encontrar o campo de valor da parcela
            # XPATH baseado no seu robô anterior
            try:
                campo_valor = self.driver.find_element(
                    By.XPATH, 
                    '//*[@id="app"]/section/main/div[2]/div/div[1]/span/form/div/span[3]/div/input'
                )
            except:
                # Tentar encontrar por placeholder ou outros atributos
                campo_valor = self.driver.find_element(
                    By.CSS_SELECTOR,
                    'input[type="text"], input[type="number"], input[placeholder*="valor"], input[placeholder*="Valor"]'
                )
            
            # Limpar campo
            campo_valor.clear()
            time.sleep(0.2)
            
            # Formatar valor para entrada (99,99 ao invés de 99.99)
            valor_para_input = f"{novo_valor_numerico:.2f}".replace('.', ',')
            
            # Digitar valor
            for char in valor_para_input:
                campo_valor.send_keys(char)
                time.sleep(0.05)
            
            # Forçar evento de mudança
            campo_valor.send_keys(Keys.TAB)
            time.sleep(0.5)
            
            print(f"✅ Campo ajustado para: {valor_para_input}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao ajustar campo manualmente: {e}")
            return False
    
    def consultar_e_esperar_valor_parcela(self, cpf, fase=1):
        """Consulta CPF e espera pelo valor da parcela"""
        try:
            prefixo = f"[FASE {fase}] "
            print(f"{prefixo}⏳ Consultando CPF {cpf}...")
            
            # Limpar e preencher CPF
            try:
                cpf_field = self.driver.find_element(By.CSS_SELECTOR, 'input[placeholder="000.000.000-00"]')
                cpf_field.click()
                time.sleep(0.5)
                cpf_field.send_keys(Keys.CONTROL + "a")
                cpf_field.send_keys(Keys.DELETE)
                time.sleep(0.1)
                
                cpf_formatado = self.formatar_cpf(cpf)
                cpf_field.send_keys(cpf_formatado)
                time.sleep(0.5)
            except:
                return None, "erro_cpf"
            
            # Clicar consultar
            try:
                consultar_btn = self.driver.find_element(By.XPATH, '//button[contains(text(), "Consultar")]')
                consultar_btn.click()
            except:
                return None, "erro_consultar"
            
            # Esperar valor da parcela (até 10 segundos)
            inicio = time.time()
            while (time.time() - inicio) < 10:
                try:
                    xpath_valor_parcela = '//*[@id="app"]/section/main/div[2]/div/div[1]/span/form/section/p[2]'
                    valor_element = self.driver.find_element(By.XPATH, xpath_valor_parcela)
                    
                    if valor_element.is_displayed():
                        valor_texto = valor_element.text.strip()
                        if valor_texto:
                            print(f"{prefixo}✅ Valor da parcela: {valor_texto}")
                            return valor_texto, "sucesso"
                except:
                    pass
                
                time.sleep(0.5)
            
            # Verificar se tem erro
            try:
                xpath_erro = "/html/body/div[2]/div"
                erro_element = self.driver.find_element(By.XPATH, xpath_erro)
                if erro_element.is_displayed():
                    texto_erro = erro_element.text.strip()
                    if texto_erro:
                        print(f"{prefixo}❌ Erro: {texto_erro}")
                        return None, "inelegivel"
            except:
                pass
            
            print(f"{prefixo}⚠️  Timeout")
            return None, "timeout"
            
        except Exception as e:
            print(f"{prefixo}❌ Erro na consulta: {e}")
            return None, "erro"
    
    def processar_cliente_com_ajuste_centavo(self, cliente, fase=1):
        """Processa um cliente com tratamento de erro de 1 centavo"""
        prefixo = f"[FASE {fase}] "
        
        print(f"{prefixo}👤 Processando: {cliente['cpf']} - {cliente['nome'][:15]}...")
        
        # Consultar cliente e pegar valor da parcela
        valor_parcela, status = self.consultar_e_esperar_valor_parcela(cliente['cpf'], fase)
        
        if status != "sucesso" or not valor_parcela:
            if fase == 1:
                cliente['status_fase1'] = status
            else:
                cliente['status_fase2'] = status
            return False
        
        # Guardar valor original da parcela
        valor_original = valor_parcela
        valor_atual = valor_original
        
        # Selecionar parcelas
        num_parcelas = self.selecionar_parcelas()
        if num_parcelas == 0:
            if fase == 1:
                cliente['status_fase1'] = "erro_parcelas"
            else:
                cliente['status_fase2'] = "erro_parcelas"
            return False
        
        # Tentar simular (com ajuste de centavo se necessário)
        tentativa = 1
        max_tentativas = 5  # Aumentei porque pode precisar ajustar várias vezes
        ajustes_realizados = 0
        
        while tentativa <= max_tentativas:
            print(f"{prefixo}🔄 Tentativa {tentativa}/{max_tentativas}")
            
            # Se não é a primeira tentativa, precisamos ajustar o campo
            if tentativa > 1:
                # Ajustar campo manualmente com o novo valor
                self.ajustar_campo_valor_parcela_manual(valor_numerico)
            
            # Clicar em simular
            if not self.clicar_simular():
                if fase == 1:
                    cliente['status_fase1'] = "erro_simular"
                else:
                    cliente['status_fase2'] = "erro_simular"
                return False
            
            # Aguardar resultado
            time.sleep(3)
            
            # Verificar se deu erro "valor maior que disponível"
            if self.verificar_erro_valor_maior_disponivel():
                print(f"{prefixo}⚠️  Erro 'valor maior que disponível' detectado!")
                
                # Ajustar 1 centavo na parcela
                novo_valor_formatado, valor_numerico = self.ajustar_parcela_1_centavo(valor_atual)
                
                # Atualizar valor atual para próxima tentativa
                valor_atual = novo_valor_formatado
                ajustes_realizados += 1
                
                print(f"{prefixo}🔧 Ajuste {ajustes_realizados}: {valor_atual}")
                
                tentativa += 1
                continue
            
            # Se não tem erro, podemos extrair valor liberado
            print(f"{prefixo}✅ Simulação bem sucedida!")
            break
        
        # Se esgotou tentativas
        if tentativa > max_tentativas:
            print(f"{prefixo}❌ Máximo de {max_tentativas} tentativas atingido")
            if fase == 1:
                cliente['status_fase1'] = "max_tentativas"
            else:
                cliente['status_fase2'] = "max_tentativas"
            return False
        
        # Extrair valor liberado
        valor_liberado = self.extrair_valor_liberado_simples()
        
        # Salvar resultados
        if fase == 1:
            cliente['status_fase1'] = 'sucesso'
            cliente['valor_parcela_fase1'] = valor_atual  # Pode ser o valor ajustado
            cliente['valor_original_fase1'] = valor_original
            cliente['parcelas_fase1'] = num_parcelas
            cliente['valor_liberado_fase1'] = valor_liberado
            cliente['ajustes_fase1'] = ajustes_realizados
        else:
            cliente['status_fase2'] = 'sucesso'
            cliente['valor_parcela_fase2'] = valor_atual  # Pode ser o valor ajustado
            cliente['valor_original_fase2'] = valor_original
            cliente['parcelas_fase2'] = num_parcelas
            cliente['valor_liberado_fase2'] = valor_liberado
            cliente['ajustes_fase2'] = ajustes_realizados
        
        print(f"{prefixo}🎯 Resultado: {num_parcelas} parcelas de {valor_atual} | Total: {valor_liberado}")
        if ajustes_realizados > 0:
            print(f"{prefixo}🔧 Ajustes necessários: {ajustes_realizados} (Original: {valor_original})")
        
        return True
    
    def extrair_valor_liberado_simples(self):
        """Extrai valor liberado - MÉTODO DIRETO E SIMPLES"""
        try:
            time.sleep(3)
            
            # Método 1: Procurar por R$ na página inteira
            page_source = self.driver.page_source
            
            # Padrões para buscar valores
            padroes = [
                r'R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # R$ 1.234,56
                r'R\$\s*(\d+,\d{2})',                  # R$ 1234,56
                r'valor[:\s]*R\$\s*([\d.,]+)',         # valor: R$ 1.234,56
                r'liberado[:\s]*R\$\s*([\d.,]+)',      # liberado: R$ 1.234,56
                r'total[:\s]*R\$\s*([\d.,]+)',         # total: R$ 1.234,56
                r'crédito[:\s]*R\$\s*([\d.,]+)',       # crédito: R$ 1.234,56
                r'aprovado[:\s]*R\$\s*([\d.,]+)',      # aprovado: R$ 1.234,56
            ]
            
            for padrao in padroes:
                correspondencias = re.findall(padrao, page_source, re.IGNORECASE)
                if correspondencias:
                    for valor in correspondencias:
                        # Verificar se é um valor razoável (entre 100 e 100.000)
                        valor_limpo = valor.replace('.', '').replace(',', '.')
                        try:
                            valor_num = float(valor_limpo)
                            if 100 <= valor_num <= 100000:
                                print(f"✅ Valor encontrado: R$ {valor}")
                                return f"R$ {valor}"
                        except:
                            pass
            
            # Método 2: Tentar XPATH específico
            try:
                xpath_valor = '//*[@id="app"]/section/main/div[2]/div/div[2]/section[1]'
                elemento = self.driver.find_element(By.XPATH, xpath_valor)
                
                if elemento.is_displayed():
                    texto = elemento.text.strip()
                    print(f"📄 Texto no XPATH: {texto}")
                    
                    if 'R$' in texto:
                        # Extrair tudo depois do R$
                        partes = texto.split('R$')
                        if len(partes) > 1:
                            valor_bruto = partes[1].strip()
                            valor_limpo = valor_bruto.split()[0] if ' ' in valor_bruto else valor_bruto
                            print(f"✅ Valor extraído: R$ {valor_limpo}")
                            return f"R$ {valor_limpo}"
            except:
                pass
            
            # Método 3: Procurar todos os elementos com R$
            try:
                elementos = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'R$')]")
                
                for elemento in elementos:
                    if elemento.is_displayed():
                        texto = elemento.text.strip()
                        if texto and len(texto) < 50:  # Textos curtos são mais prováveis
                            match = re.search(r'R\$\s*([\d.,]+)', texto)
                            if match:
                                valor = match.group(1)
                                print(f"✅ Valor em elemento: R$ {valor}")
                                return f"R$ {valor}"
            except:
                pass
            
            print("⚠️  Não encontrou valor liberado na tela")
            return "Valor não encontrado"
            
        except Exception as e:
            print(f"❌ Erro ao extrair valor: {e}")
            return "Erro na extração"
    
    def processar_lista(self, lista_clientes, fazer_reconsulta=True):
        """Processa lista de clientes - FASE 1 e FASE 2 INDEPENDENTES"""
        print(f"💰 Consultando {len(lista_clientes)} clientes")
        
        # 🔴 IMPORTANTE: Cada fase começa DO ZERO!
        # Não vamos passar dados de uma fase para outra
        
        resultados_fase1 = []
        
        # ========== FASE 1 ==========
        print("\n" + "="*60)
        print("🔄 FASE 1 - CONSULTA INICIAL (COMEÇA DO ZERO)")
        print("="*60)
        
        # Setup driver para Fase 1
        self.setup_driver()
        
        # Login para Fase 1
        if not self.login_admin():
            print("❌ Login falhou na Fase 1")
            self.driver.quit()
            return []
        
        # Acessar simulação para Fase 1
        if not self.acessar_simulacao():
            print("❌ Não acessou simulação na Fase 1")
            self.driver.quit()
            return []
        
        for i, cliente in enumerate(lista_clientes, 1):
            print(f"\n[FASE1 - {i}/{len(lista_clientes)}] {cliente['nome'][:15]}...")
            
            # 🔴 CRÍTICO: Criar NOVO objeto para Fase 1
            # Não vamos modificar o cliente original
            cliente_fase1 = {
                'cpf': cliente['cpf'],
                'nome': cliente['nome'],
                'telefone': cliente['telefone'],
                'status_fase1': 'pendente',
                'valor_parcela_fase1': None,
                'valor_original_fase1': None,
                'parcelas_fase1': None,
                'valor_liberado_fase1': None,
                'ajustes_fase1': 0
            }
            
            # Processar na Fase 1 (começa do zero)
            sucesso = self.processar_cliente_com_ajuste_centavo(cliente_fase1, fase=1)
            
            resultados_fase1.append(cliente_fase1)
            
            time.sleep(1)
        
        # Fechar driver da Fase 1
        self.driver.quit()
        
        # Estatísticas da Fase 1
        print(f"\n📊 ESTATÍSTICAS FASE 1:")
        sucessos_fase1 = len([r for r in resultados_fase1 if r['status_fase1'] == 'sucesso'])
        ajustes_fase1 = sum(r['ajustes_fase1'] for r in resultados_fase1)
        
        print(f"   ✅ Sucessos: {sucessos_fase1}/{len(resultados_fase1)}")
        print(f"   🔧 Ajustes realizados: {ajustes_fase1}")
        
        resultados_finais = resultados_fase1
        
        # ========== FASE 2 ==========
        if fazer_reconsulta:
            print("\n" + "="*60)
            print("🔄 FASE 2 - RECONSULTA COMPLETA (COMEÇA DO ZERO NOVAMENTE)")
            print("="*60)
            print("ℹ️  Executando CONSULTA COMPLETA novamente para todos os clientes")
            print("ℹ️  Cada cliente começa DO ZERO na Fase 2")
            
            # Setup NOVO driver para Fase 2
            self.setup_driver()
            
            # Login para Fase 2
            if not self.login_admin():
                print("❌ Login falhou na Fase 2")
                self.driver.quit()
                return resultados_finais
            
            # Acessar simulação para Fase 2
            if not self.acessar_simulacao():
                print("❌ Não acessou simulação na Fase 2")
                self.driver.quit()
                return resultados_finais
            
            for i, cliente_original in enumerate(lista_clientes, 1):
                print(f"\n[FASE2 - {i}/{len(lista_clientes)}] {cliente_original['nome'][:15]}...")
                
                # 🔴 CRÍTICO: Criar NOVO objeto para Fase 2
                # Começa COMPLETAMENTE DO ZERO
                cliente_fase2 = {
                    'cpf': cliente_original['cpf'],
                    'nome': cliente_original['nome'],
                    'telefone': cliente_original['telefone'],
                    'status_fase2': 'pendente',
                    'valor_parcela_fase2': None,
                    'valor_original_fase2': None,
                    'parcelas_fase2': None,
                    'valor_liberado_fase2': None,
                    'ajustes_fase2': 0
                }
                
                # Processar na Fase 2 (começa do zero)
                sucesso = self.processar_cliente_com_ajuste_centavo(cliente_fase2, fase=2)
                
                # Combinar resultados da Fase 1 e Fase 2
                for idx, resultado in enumerate(resultados_finais):
                    if resultado['cpf'] == cliente_fase2['cpf']:
                        # 🔴 COMBINAR, mas manter os dados da Fase 1 INTACTOS
                        resultados_finais[idx].update({
                            'status_fase2': cliente_fase2['status_fase2'],
                            'valor_parcela_fase2': cliente_fase2['valor_parcela_fase2'],
                            'valor_original_fase2': cliente_fase2['valor_original_fase2'],
                            'parcelas_fase2': cliente_fase2['parcelas_fase2'],
                            'valor_liberado_fase2': cliente_fase2['valor_liberado_fase2'],
                            'ajustes_fase2': cliente_fase2['ajustes_fase2']
                        })
                        break
                
                time.sleep(1)
            
            # Fechar driver da Fase 2
            self.driver.quit()
            
            # Estatísticas da Fase 2
            print(f"\n📊 ESTATÍSTICAS FASE 2:")
            sucessos_fase2 = len([r for r in resultados_finais if r.get('status_fase2') == 'sucesso'])
            ajustes_fase2 = sum(r.get('ajustes_fase2', 0) for r in resultados_finais)
            
            print(f"   ✅ Sucessos: {sucessos_fase2}/{len(resultados_finais)}")
            print(f"   🔧 Ajustes realizados: {ajustes_fase2}")
            
            # Comparação entre fases
            print(f"\n📈 COMPARAÇÃO ENTRE FASES:")
            
            # Clientes com sucesso em AMBAS as fases
            sucesso_ambas = len([r for r in resultados_finais 
                                if r['status_fase1'] == 'sucesso' and r.get('status_fase2') == 'sucesso'])
            
            # Clientes recuperados na Fase 2
            recuperados = len([r for r in resultados_finais 
                             if r['status_fase1'] != 'sucesso' and r.get('status_fase2') == 'sucesso'])
            
            # Clientes que pioraram na Fase 2
            pioraram = len([r for r in resultados_finais 
                          if r['status_fase1'] == 'sucesso' and r.get('status_fase2') != 'sucesso'])
            
            print(f"   ✅ Sucesso em ambas: {sucesso_ambas}")
            print(f"   🎉 Recuperados na Fase 2: {recuperados}")
            print(f"   ⚠️  Pioraram na Fase 2: {pioraram}")
            
            # Mostrar alguns casos interessantes
            print(f"\n🔍 CASOS INTERESSANTES:")
            
            # Clientes que precisaram ajustar em UMA fase mas não na outra
            ajuste_fase1_nao_fase2 = []
            ajuste_fase2_nao_fase1 = []
            
            for r in resultados_finais:
                if r.get('ajustes_fase1', 0) > 0 and r.get('ajustes_fase2', 0) == 0:
                    ajuste_fase1_nao_fase2.append(r)
                elif r.get('ajustes_fase1', 0) == 0 and r.get('ajustes_fase2', 0) > 0:
                    ajuste_fase2_nao_fase1.append(r)
            
            if ajuste_fase1_nao_fase2:
                print(f"   ⚙️  Ajuste só na Fase 1: {len(ajuste_fase1_nao_fase2)} clientes")
                for cliente in ajuste_fase1_nao_fase2[:3]:  # Mostra só 3
                    print(f"      {cliente['cpf']} - {cliente['nome'][:15]}...")
            
            if ajuste_fase2_nao_fase1:
                print(f"   ⚙️  Ajuste só na Fase 2: {len(ajuste_fase2_nao_fase1)} clientes")
                for cliente in ajuste_fase2_nao_fase1[:3]:  # Mostra só 3
                    print(f"      {cliente['cpf']} - {cliente['nome'][:15]}...")
        
        print(f"\n✅ PROCESSAMENTO COMPLETO CONCLUÍDO!")
        print(f"📋 Total de clientes processados: {len(resultados_finais)}")
        
        return resultados_finais
    
    def salvar_resultados_excel(self, resultados, filename):
        """Salva resultados em Excel com coluna de ajustes"""
        try:
            df = pd.DataFrame(resultados)
            
            # Reordenar colunas para melhor visualização
            colunas_preferencia = [
                'cpf', 'nome', 'telefone',
                'status_fase1', 'valor_original_fase1', 'valor_parcela_fase1', 
                'parcelas_fase1', 'valor_liberado_fase1', 'ajustes_fase1',
                'status_fase2', 'valor_original_fase2', 'valor_parcela_fase2',
                'parcelas_fase2', 'valor_liberado_fase2', 'ajustes_fase2'
            ]
            
            # Filtrar apenas colunas que existem
            colunas_existentes = [c for c in colunas_preferencia if c in df.columns]
            
            # Adicionar outras colunas no final
            outras_colunas = [c for c in df.columns if c not in colunas_existentes]
            
            df = df[colunas_existentes + outras_colunas]
            df.to_excel(filename, index=False)
            
            print(f"💾 Excel salvo: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Erro ao salvar Excel: {e}")
            return None

# Teste da funcionalidade de ajuste
if __name__ == "__main__":
    robo = RoboConsultas()
    
    # Testar ajuste de 1 centavo
    print("\n🔧 TESTANDO AJUSTE DE 1 CENTAVO NA PARCELA")
    print("="*40)
    
    teste_valores = [
        "R$ 1.234,56",
        "R$ 500,00", 
        "R$ 99,99",
        "R$ 1234,56",
        "R$ 245,76"
    ]
    
    for valor in teste_valores:
        ajustado, numerico = robo.ajustar_parcela_1_centavo(valor)
        print(f"{valor} → {ajustado} (R$ {numerico:.2f})")