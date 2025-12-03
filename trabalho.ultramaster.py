import itertools
import sys

# ============================
# LEITURA DA GRAMÁTICA
# ============================

def ler_gramatica(caminho):
    """
    Lê gramática no formato:

    <lista de variáveis>
    <lista de terminais>
    <símbolo inicial>
    <produções no formato: Variável Produção>
    """

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = [linha.strip() for linha in f if linha.strip() and not linha.startswith("#")]

        if len(linhas) < 3:
            raise ValueError("Arquivo inválido: faltam seções obrigatórias.")

        # 1) Variáveis
        variaveis = linhas[0].split()

        # 2) Terminais
        terminais = linhas[1].split()

        # 3) Símbolo inicial
        inicial = linhas[2]

        if inicial not in variaveis:
            raise ValueError("Símbolo inicial não está na lista de variáveis.")

        # 4) Produções
        gramatica = {V: [] for V in variaveis}

        for linha in linhas[3:]:
            partes = linha.split(None, 1)

            if len(partes) != 2:
                raise ValueError(f"Linha inválida: {linha}")

            var, prod = partes

            if var not in variaveis:
                raise ValueError(f"Variável '{var}' usada em produção mas não listada nas variáveis.")

            gramatica[var].append(prod)

        return gramatica, inicial, variaveis, terminais

    except FileNotFoundError:
        print(f"Erro: arquivo '{caminho}' não encontrado.")
        sys.exit(1)


    except FileNotFoundError:
        print(f"Erro: arquivo '{caminho}' não encontrado")
        sys.exit(1)


def exibir_gramatica(G, titulo=""):
    """Exibe a gramática formatada"""
    if titulo:
        print(f"\n{'='*50}")
        print(f"{titulo}")
        print('='*50)
    
    # Ordena as chaves para exibição bonita, mas mantém lógica interna intacta
    for var in sorted(G.keys()):
        for prod in G[var]:
            print(f"{var} {prod}")


def salvar_gramatica(G, caminho):
    """Salva a gramática em arquivo"""
    with open(caminho, "w", encoding="utf-8") as f:
        for var in sorted(G.keys()):
            for prod in G[var]:
                f.write(f"{var} {prod}\n")


# ============================
# PARTE 1 – LIMPEZA
# ============================

def remover_vazias(G, simbolo_inicial):
    """Remove produções vazias (eps), exceto no símbolo inicial se necessário"""
    G_copy = {A: list(prods) for A, prods in G.items()}
    
    # 1. Encontrar variáveis anuláveis
    anulaveis = set()
    mudou = True
    
    while mudou:
        mudou = False
        for A in G_copy:
            if "eps" in G_copy[A]:
                if A not in anulaveis:
                    anulaveis.add(A)
                    mudou = True
            else:
                for prod in G_copy[A]:
                    # Se todos os símbolos da produção são anuláveis
                    if prod and all(c in anulaveis for c in prod if c.isupper()):
                        # Verifica se não há terminais impedindo
                        if len(prod) > 0 and all(c in anulaveis or c.islower() for c in prod):
                            # Se tem terminal (islower), não é anulável só por variáveis
                            # Lógica simplificada: Se tem terminal, não é anulável (exceto se o terminal for eps, que já tratamos)
                            pass 
                        
                        # Verificação correta: se SÓ tem variáveis e todas são anuláveis
                        so_variaveis = all(c.isupper() for c in prod)
                        if so_variaveis and all(c in anulaveis for c in prod):
                             if A not in anulaveis:
                                anulaveis.add(A)
                                mudou = True

    # 2. Criar novas produções
    G_sem_vazias = {}
    
    for A in G_copy:
        G_sem_vazias[A] = set()
        for prod in G_copy[A]:
            if prod == "eps":
                # Só manter eps se for o símbolo inicial
                if A == simbolo_inicial and A in anulaveis:
                    G_sem_vazias[A].add("eps")
            else:
                G_sem_vazias[A].add(prod)
                
                # Gera variantes removendo anuláveis
                indices_anulaveis = [i for i, c in enumerate(prod) if c in anulaveis]
                
                for r in range(1, len(indices_anulaveis) + 1):
                    for combo in itertools.combinations(indices_anulaveis, r):
                        nova_prod = ''.join(c for i, c in enumerate(prod) if i not in combo)
                        if nova_prod:
                            G_sem_vazias[A].add(nova_prod)
                        elif A == simbolo_inicial:
                            # Se a produção ficou vazia e é o inicial, vira eps
                            G_sem_vazias[A].add("eps")
    
    return {A: sorted(list(G_sem_vazias[A])) for A in G_sem_vazias}


def remover_unidades(G):
    """Remove produções unidade A -> B, onde A e B são variáveis únicas."""
    
    unidades = {A: set() for A in G}
    nao_unidades = {A: set() for A in G}

    # Identifica produções unidade corretamente
    for A in G:
        for prod in G[A]:
            # Produção unidade só se tiver exatamente UM símbolo e for variável
            if len(prod) == 1 and prod[0].isupper():
                unidades[A].add(prod)
            else:
                nao_unidades[A].add(prod)

    # Fecho transitivo
    mudou = True
    while mudou:
        mudou = False
        for A in unidades:
            for B in list(unidades[A]):
                if B in G:
                    for prod in G[B]:

                        # Caso 1: B -> C (unidade)
                        if len(prod) == 1 and prod[0].isupper():
                            if prod not in unidades[A] and prod != A:
                                unidades[A].add(prod)
                                mudou = True

                        # Caso 2: B -> α (produção normal)
                        else:
                            if prod not in nao_unidades[A]:
                                nao_unidades[A].add(prod)
                                mudou = True

    # Retorna gramática sem produções-unidade
    return {A: sorted(list(nao_unidades[A])) for A in G}



def remover_inuteis(G, simbolo_inicial):
    """Remove produções inúteis (não geram terminais ou inalcançáveis)"""
    
    # 1. Variáveis Geradoras (Produtivas)
    produtivas = set()
    mudou = True
    
    while mudou:
        mudou = False
        for A in G:
            if A in produtivas: continue
            for prod in G[A]:
                if prod == "eps":
                    produtivas.add(A); mudou = True; break
                
                # Verifica se símbolos são terminais ou variáveis já marcadas como produtivas
                pode_gerar = True
                for c in prod:
                    if c.isupper() and c not in produtivas:
                        pode_gerar = False
                        break
                
                if pode_gerar:
                    produtivas.add(A); mudou = True; break
    
    # Filtra gramática mantendo apenas produtivas
    G_temp = {}
    for A in G:
        if A in produtivas:
            G_temp[A] = []
            for prod in G[A]:
                if all(c not in G or c in produtivas for c in prod if c.isupper()):
                    G_temp[A].append(prod)

    # 2. Variáveis Acessíveis (Inalcançáveis) - Começando do Símbolo Inicial Dinâmico
    acessiveis = set()
    if simbolo_inicial in G_temp:
        acessiveis.add(simbolo_inicial)
    
    mudou = True
    while mudou:
        mudou = False
        # Copia para evitar erro de iteração
        for A in list(acessiveis):
            if A in G_temp:
                for prod in G_temp[A]:
                    for c in prod:
                        if c.isupper() and c not in acessiveis:
                            acessiveis.add(c)
                            mudou = True
    
    # Filtra final
    G_final = {}
    for A in G_temp:
        if A in acessiveis:
            G_final[A] = G_temp[A]
            
    return G_final


# ============================
# PARTE 2 – CHOMSKY (CNF)
# ============================

def para_CNF(G):
    """Converte para Forma Normal de Chomsky"""
    G = eliminar_terminais_mistos(G)
    G = binarizar(G)
    return G


def eliminar_terminais_mistos(G):
    novos_vars = {}
    G_novo = {}
    contador = 0
    
    for A in G:
        G_novo[A] = []
        for prod in G[A]:
            if prod == "eps" or len(prod) == 1:
                G_novo[A].append(prod)
            else:
                nova_prod = ""
                for c in prod:
                    if c.islower(): # é terminal
                        if c not in novos_vars:
                            contador += 1
                            novos_vars[c] = f"T{contador}"
                        nova_prod += novos_vars[c]
                    else:
                        nova_prod += c
                G_novo[A].append(nova_prod)
    
    # Adiciona as produções dos novos terminais isolados (Ex: T1 -> a)
    for term, var in novos_vars.items():
        G_novo[var] = [term]
        
    return G_novo


def binarizar(G):
    G_novo = {}
    contador = 0
    
    for A in G:
        G_novo[A] = []
        for prod in G[A]:
            if len(prod) <= 2 or prod == "eps":
                G_novo[A].append(prod)
            else:
                # Quebra cadeias longas: A -> BCDE vira A -> BX1, X1 -> CX2...
                lista_simbolos = []
                # Tokenizar variáveis (como T1, T2) ou letras simples
                i = 0
                while i < len(prod):
                    if prod[i].isupper() and i+1 < len(prod) and prod[i+1].isdigit():
                        lista_simbolos.append(prod[i:i+2]) # Pega T1, X2...
                        i += 2
                    else:
                        lista_simbolos.append(prod[i])
                        i += 1
                
                # Binarização
                if len(lista_simbolos) <= 2:
                    G_novo[A].append(prod)
                    continue

                curr_var = A
                for k in range(len(lista_simbolos) - 2):
                    contador += 1
                    nova_var = f"X{contador}"
                    # A -> Símbolo + NovaVar
                    if curr_var not in G_novo: G_novo[curr_var] = []
                    G_novo[curr_var].append(lista_simbolos[k] + nova_var)
                    curr_var = nova_var
                    G_novo[curr_var] = [] # Inicializa
                
                # Últimos dois
                if curr_var not in G_novo: G_novo[curr_var] = []
                G_novo[curr_var].append(lista_simbolos[-2] + lista_simbolos[-1])
                
    return G_novo


# ============================
# PARTE 3 – TESTE (DERIVAÇÃO)
# ============================

def derivar_palavra(G_original, G_cnf, palavra, simbolo_inicial):
    """Testa derivação começando do simbolo_inicial detectado"""
    
    if not palavra:
        if simbolo_inicial in G_original and "eps" in G_original[simbolo_inicial]:
            print(f"✓ Palavra vazia aceita ({simbolo_inicial} -> eps)")
            return True
        print("✗ Palavra vazia rejeitada")
        return False
        
    print(f"\nTestando: '{palavra}' (Início: {simbolo_inicial})")
    
    fila = [(simbolo_inicial, [])]
    visitados = set()
    passos_limite = 2000 
    
    while fila:
        atual, hist = fila.pop(0)
        
        # ================================
        # SE CHEGOU NA PALAVRA ALVO
        # ================================
        if atual == palavra:
            print("\n✓ SUCESSO! Palavra gerada.\n")

            # IMPRIME TODOS OS PASSOS DO HISTÓRICO
            for passo in hist:
                print(passo)

            print(f"Resultado: {atual}  (cadeia terminal igual à palavra alvo -> sucesso)")
            return True
        
        if len(atual) > len(palavra) + 5:
            continue
            
        hash_estado = (atual, len(hist))
        if hash_estado in visitados or len(hist) > 50:
            continue
        visitados.add(hash_estado)
        
        # Primeira variável à esquerda
        idx_var = -1
        var_nome = ""
        
        for i, char in enumerate(atual):
            if char.isupper():
                idx_var = i
                if i+1 < len(atual) and atual[i+1].isdigit():
                    var_nome = atual[i:i+2]
                else:
                    var_nome = char
                break
        
        if idx_var == -1:
            continue 
        
        if var_nome in G_cnf:
            prefixo = atual[:idx_var]
            sufixo = atual[idx_var + len(var_nome):]
            
            for corpo in G_cnf[var_nome]:
                novo_estado = prefixo + corpo + sufixo
                
                # Verificação de prefixo terminal válido
                prefixo_terminal = ""
                for c in novo_estado:
                    if c.islower(): prefixo_terminal += c
                    else: break
                
                if not palavra.startswith(prefixo_terminal):
                    continue
                
                # ================================
                # ADICIONA PASSO AO HISTÓRICO
                # ================================
                passo_formatado = (
                    f"Palavra antes: {atual}\n"
                    f"Regra aplicada: {var_nome} -> {corpo}\n"
                    f"Palavra depois: {novo_estado}\n"
                )
                
                fila.append((novo_estado, hist + [passo_formatado]))

    print(f"✗ Falha: Palavra '{palavra}' não gerada.")
    return False






# ============================
# MAIN
# ============================

def main():
    print("="*50)
    print("PROCESSADOR DE GRAMÁTICAS DO SAULAO")
    print("="*50)
    
    caminho = input("Arquivo de entrada [entrada.txt]: ").strip() or "entrada.txt"
    
    # 1. Leitura com detecção do símbolo inicial
    gramatica, simbolo_inicial, variaveis, terminais = ler_gramatica(caminho)
    
    print(f"\n[INFO] Símbolo Inicial detectado: '{simbolo_inicial}'")
    print(f"[INFO] Variáveis: {variaveis}")
    print(f"[INFO] Terminais: {terminais}")
    
    exibir_gramatica(gramatica, "ORIGINAL")
    
    # 2. Limpeza
    print("\n=== LIMPANDO GRAMÁTICA ===")
    
    g_limpa = remover_vazias(gramatica, simbolo_inicial)
    g_limpa = remover_unidades(g_limpa)
    g_limpa = remover_inuteis(g_limpa, simbolo_inicial)
    
    exibir_gramatica(g_limpa, "LIMPA (SEM EPS, SEM UNITÁRIAS, SEM INÚTEIS)")
    salvar_gramatica(g_limpa, "saida_limpa.txt")
    
    # 3. Forma Normal de Chomsky
    print("\n=== CONVERTENDO PARA CNF ===")
    
    g_cnf = para_CNF(g_limpa)
    exibir_gramatica(g_cnf, "FORMA NORMAL DE CHOMSKY")
    salvar_gramatica(g_cnf, "saida_cnf.txt")
    
    # 4. Teste
    print("\n" + "="*50)
    print("MODO DE TESTE (Digite 'sair' para encerrar)")
    print("="*50)
    
    while True:
        p = input("\nPalavra para testar: ").strip()
        if p.lower() in ["sair", "exit"]:
            break

        # importante: agora a derivação é feita a partir da gramática ORIGINAL
        # (a pedido do usuário)
        derivar_palavra(gramatica, g_cnf, p, simbolo_inicial)


if __name__ == "__main__":
    main()
