# 03 — Template do Relatório de Auditoria (Fase 2)

Use **exatamente** este formato. Findings ordenados por severidade (CRITICAL → HIGH →
MEDIUM → LOW). Todo finding precisa de `File: <arquivo>:<linha(s)>`.

## Cabeçalho + corpo

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Título do anti-pattern>
File: <arquivo>:<linha(s)>
Description: <o problema concreto, em 1–2 linhas>
Impact: <consequência prática>
Recommendation: <ação corretiva; cite o padrão do playbook ou a API moderna>

### [CRITICAL] <próximo finding>
...

### [HIGH] <...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

================================
Total: <N> findings
================================
```

## Regras de preenchimento

- **Ordenação:** estritamente CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade,
  agrupe por arquivo quando fizer sentido.
- **Linhas exatas:** se o mesmo problema ocorre em muitas linhas, liste as principais
  (ex.: `models.py:28, 47-50, 110-111`) — não invente linhas; cite as reais.
- **APIs deprecated:** inclua-as como findings normais, com a API moderna na recomendação.
- **Mínimos:** ≥5 findings e ≥1 CRITICAL/HIGH. Se um projeto realmente não tiver CRITICAL,
  registre isso explicitamente em vez de inflar a severidade.
- **Sem ruído:** cada finding deve ser acionável. Evite findings genéricos ("código
  desorganizado"); aponte o quê, onde e como corrigir.
- **Persistência:** salve o relatório em `reports/audit-<nome-do-projeto>.md` por padrão
  (crie o diretório `reports/` se necessário), mantendo exatamente este formato, e informe o
  caminho ao usuário. **Proponha esse caminho sem esperar que o usuário peça**; se ele indicar
  outro, use o dele. O arquivo do relatório é a única escrita permitida na Fase 2.

## Encerramento da fase (obrigatório)

Depois de exibir o relatório, **pare** e pergunte literalmente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Não modifique nenhum arquivo **de código** do projeto antes da resposta `y` — apenas o
arquivo do relatório em `reports/` pode ser escrito nesta fase.
