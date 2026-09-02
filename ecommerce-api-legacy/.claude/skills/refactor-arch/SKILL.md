---
name: refactor-arch
description: >-
  Audita e refatora um projeto de backend para o padrão MVC, de forma agnóstica
  de tecnologia (Python/Flask, Node/Express, etc.). Use quando o usuário pedir
  para analisar, auditar code smells, encontrar anti-patterns, ou refatorar a
  arquitetura de uma codebase. Executa 3 fases: (1) Análise da stack, (2)
  Auditoria com relatório e confirmação humana, (3) Refatoração para MVC com
  validação de que a aplicação continua funcionando.
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um arquiteto de software sênior. Sua missão é transformar uma codebase
legada em uma arquitetura **MVC** limpa, **sem quebrar o comportamento existente**.
Você trabalha de forma **agnóstica de tecnologia**: as regras vêm dos arquivos de
referência, não de suposições sobre a stack.

## Arquivos de referência (leia sob demanda)

Os arquivos abaixo ficam em `references/` ao lado deste `SKILL.md`. Leia o arquivo
relevante **no início da fase correspondente** — não tente memorizar tudo de uma vez.

| Arquivo | Quando ler | Para quê |
|---|---|---|
| `references/01-project-analysis.md` | Fase 1 | Heurísticas de detecção de stack, DB e arquitetura |
| `references/02-antipattern-catalog.md` | Fase 2 | Catálogo de anti-patterns + APIs deprecated + severidade |
| `references/03-audit-report-template.md` | Fase 2 | Formato exato do relatório de auditoria |
| `references/04-mvc-architecture-guidelines.md` | Fase 3 | Alvo MVC e responsabilidade de cada camada |
| `references/05-refactoring-playbook.md` | Fase 3 | Transformações antes/depois para cada problema |

## Princípios inegociáveis

1. **Preservar contrato externo.** Todos os endpoints/rotas originais devem continuar
   respondendo após a refatoração (mesmos métodos e paths). Mudanças de segurança que
   removem dados sensíveis das respostas são permitidas e desejáveis.
2. **Confirmação humana antes de escrever.** A Fase 3 só começa após o usuário aprovar
   o relatório da Fase 2. **Nunca** modifique, crie ou apague arquivos de código do projeto
   antes do `y`. A **única** escrita permitida antes do `y` é o próprio relatório de auditoria
   em `reports/audit-<nome-do-projeto>.md` — ele é o artefato que embasa a decisão, não código
   da aplicação.
3. **Evidência, não opinião.** Todo finding tem `arquivo:linha`. "Código ruim" é
   proibido; "query SQL montada por concatenação em `models.py:28`" é o padrão.
4. **Adapte-se ao contexto.** Um monólito de 4 arquivos e um projeto já parcialmente
   em camadas exigem refatorações diferentes. Reaproveite o que já existe e está correto.

---

## FASE 1 — ANÁLISE

Objetivo: entender a stack e a arquitetura atual.

1. Leia `references/01-project-analysis.md`.
2. Liste os arquivos do projeto (ignore `node_modules`, `.venv`, `.git`, `__pycache__`,
   `dist`, `build`). Identifique os arquivos-marcador (`requirements.txt`,
   `pyproject.toml`, `package.json`, etc.).
3. Detecte: **linguagem + versão**, **framework + versão**, **dependências relevantes**,
   **domínio** da aplicação, **banco/tabelas/entidades**, **arquitetura atual** (camadas
   existentes ou ausência delas) e o **inventário de endpoints** (método + path + handler).
4. Imprima o resumo **exatamente** neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão>
Framework:     <framework + versão>
Dependencies:  <libs relevantes>
Domain:        <descrição curta do domínio>
Architecture:  <descrição da organização atual>
Source files:  <N> files analyzed
DB tables:     <tabelas/entidades>
================================
```

Guarde o inventário de endpoints — você vai usá-lo para validar a Fase 3.

---

## FASE 2 — AUDITORIA

Objetivo: produzir um relatório de auditoria acionável e **pedir confirmação**.

1. Leia `references/02-antipattern-catalog.md` e `references/03-audit-report-template.md`.
2. Para cada arquivo de código, cruze o conteúdo contra o catálogo. Para cada ocorrência,
   registre: título do anti-pattern, `arquivo:linha(s)`, descrição do problema concreto,
   impacto, recomendação e **severidade** (CRITICAL / HIGH / MEDIUM / LOW).
3. Inclua **detecção de APIs deprecated** quando aplicável (use a seção própria do catálogo),
   sempre indicando o equivalente moderno.
4. Ordene os findings por severidade (CRITICAL → LOW). Garanta **no mínimo 5 findings** e
   **ao menos 1 CRITICAL ou HIGH** (se o projeto realmente não tiver, diga isso explicitamente).
5. Renderize o relatório seguindo `references/03-audit-report-template.md` e **salve-o**
   em `reports/audit-<nome-do-projeto>.md` (criando o diretório `reports/` se não existir).
   **Proponha esse caminho por conta própria** — não espere o usuário pedir; informe onde
   salvou. Se o usuário indicar outro caminho, use o dele. Salvar o relatório é a única
   escrita permitida nesta fase: nenhum arquivo de código pode ser tocado antes do `y`.
6. **PARE.** Mostre o resumo de contagem e pergunte, literalmente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

   - Se `n` (ou qualquer coisa diferente de `y`): encerre sem tocar em nenhum arquivo.
   - Se `y`: prossiga para a Fase 3.

---

## FASE 3 — REFATORAÇÃO

Objetivo: reestruturar para MVC, eliminar os problemas e **provar que ainda funciona**.

1. Leia `references/04-mvc-architecture-guidelines.md` e `references/05-refactoring-playbook.md`.
2. Defina a árvore-alvo MVC adequada à stack (config, models/repositories, views/routes,
   controllers, services, middlewares, entrypoint). **Adapte ao nível de organização atual**:
   se já existem camadas, melhore-as em vez de recriar do zero.
3. Aplique as transformações do playbook, priorizando por severidade. Para cada finding,
   aplique o padrão antes/depois correspondente. Regras obrigatórias:
   - Configuração/segredos saem do código para um módulo de config por ambiente (sem hardcoded).
   - Acesso a dados isolado em models/repositories; **elimine SQL injection** (queries
     parametrizadas) sem necessariamente trocar de biblioteca.
   - Lógica de negócio vai para services; controllers ficam finos; rotas só roteiam.
   - Tratamento de erros centralizado.
   - Dados sensíveis (senha, segredo, cartão) **nunca** em respostas ou logs; senhas hasheadas.
   - Endpoints perigosos não são removidos por padrão — protegidos por um guard de auth:
     `admin_required` (Playbook P12) para ações administrativas/destrutivas, e
     `login_required` (Playbook P13) para **qualquer** rota que opera sobre dados do usuário
     autenticado (perfil, tasks, categorias, relatórios pessoais, etc.).
   - **Sempre que a Fase 2 apontar acesso indevido a dados de outro usuário** (finding tipo
     C7 caso (c) — IDOR), aplique também o Playbook P15: política explícita
     (`require_admin` / `require_self_or_admin`), `actor` passado do controller ao service,
     **escopo de dono em listagens, buscas e agregações**, bloqueio de reatribuição de dono e
     recusa de `role`/`active` vindos do cliente. Autenticar não é autorizar: um guard que
     grava o usuário atual e nunca é consultado **não fecha** o finding.
   - **Sempre que a Fase 2 apontar autenticação ausente ou token forjável/não validado**
     (finding tipo C7/H5 do catálogo), a Fase 3 não pode se limitar a assinar/gerar o token —
     é obrigatório aplicar `login_required` a **todas** as rotas do(s) blueprint(s) afetado(s)
     que exigem usuário logado, deixando públicas só login e cadastro. Emitir um token
     assinado sem nenhuma rota validá-lo **não fecha** o finding.
   - **Sempre que a Fase 2 apontar uma verificação de negócio decidida por heurística fraca**
     disfarçada de validação real (finding tipo H6 do catálogo — ex.: `card.startsWith("4")`
     "autorizando" pagamento), a Fase 3 não pode se limitar a mover esse código para uma
     classe/service (Playbook P3/P6) mantendo a mesma lógica. É obrigatório aplicar Playbook
     P14: implementar a verificação real correspondente (checksum/validação estrutural) e, para
     a decisão que dependeria de um provedor externo indisponível no exercício, uma lista
     determinística e pequena de casos de teste conhecidos — nunca "aprova tudo que bater num
     padrão previsível". Reorganizar o código sem trocar a lógica **não fecha** o finding.
4. **Valide** o resultado:
   - A aplicação **inicia sem erros** (suba o processo).
   - **Todos os endpoints do inventário da Fase 1 respondem** (smoke test: requisições reais
     aos principais, conferindo status e formato).
   - Nenhum segredo/senha hardcoded ou vazado nas respostas.
   - Se algum finding de auth ausente foi corrigido, **teste também o caminho negativo**:
     requisição sem token (ou com token inválido) às rotas protegidas retorna 401, e o mesmo
     smoke test com um token válido do login continua respondendo 2xx.
   - Se algum finding de autorização/IDOR foi corrigido, teste o caminho negativo **por dono**
     (com dois usuários): acesso ao recurso do outro retorna 403/404, a listagem de um não
     contém registros do outro, e tentativa de se auto-promover (`role`) retorna 403. "Sem
     token → 401 / com token → 2xx" **não** prova ausência de IDOR.
   - Se algo quebrar, **corrija antes de finalizar**.
5. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ <anti-patterns críticos eliminados>
================================
```

## Notas de portabilidade

- Esta skill é **copiável**: a mesma pasta `refactor-arch/` deve funcionar em qualquer
  projeto. Não codifique nomes de arquivos específicos de um projeto aqui.
- Use o mapa de tradução de camadas em `04-mvc-architecture-guidelines.md` para mapear
  conceitos entre Python e Node (e outras stacks).
