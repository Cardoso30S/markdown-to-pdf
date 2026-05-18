# Instruções do Projeto

## Fluxo de Git

Após cada `git push` ou criação de PR, **sempre** mesclar a branch na `main` automaticamente usando a ferramenta GitHub MCP (`mcp__github__merge_pull_request`).

Passos obrigatórios após push:
1. Verificar se existe PR aberto para a branch atual
2. Se não existir, criar um PR (draft: false)
3. Mesclar o PR na `main` (merge method: `squash` ou `merge`)
4. Confirmar a mesclagem ao usuário
