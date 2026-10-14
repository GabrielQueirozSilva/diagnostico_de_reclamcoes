# Dicionário de dados

| Campo | Descrição | Tipo (banco) | Valores / observações | Status |
|---|---|---|---|---|
| `regiao` | Região do consumidor | texto | `SE`, `NE`, `S`, `CO`, `N` | ok |
| `uf` | Estado do consumidor | texto(2) | Sigla | ok |
| `cidade` | Cidade do consumidor | texto | Sem nulos | ok |
| `sexo` | Sexo do consumidor | texto | `M`, `F` `O` | ok |
| `faixa_etaria` | Faixa de idade do consumidor | texto | `<=20`, `21-30`, `31-40`, `41-50`, `51-60`, `61-70`, `>70` | ok |
| `data_finalizacao` | Data em que a reclamação foi finalizada | data | Formato original ISO (AAAA-MM-DD); em agosto/2026 vai de 01/08 a 31/08 | ok |
| `tempo_resposta` | Tempo que a empresa levou para responder | número | Nulo = empresa não respondeu; valores de 0 a 11; unidade em dias | ok |
| `nome_fantasia` | Empresa reclamada | texto | | ok |
| `segmento_de_mercado` | Setor da empresa | texto | 1º nível da hierarquia | ok |
| `area` | Área dentro do segmento | texto | 2º nível | ok |
| `assunto` | Assunto da reclamação | texto | 3º nível | ok |
| `grupo_problema` | Agrupamento do problema | texto | 4º nível | ok |
| `problema` | Problema específico | texto | 5º nível | ok |
| `como_comprou_contratou` | Forma como o consumidor comprou ou contratou | texto | lista de texto | ok |
| `procurou_empresa` | Se o consumidor tentou resolver direto com a empresa antes | texto | `S` ou `N` | ok |
| `respondida` | Se a empresa respondeu | texto | `S` / `N` | ok |
| `situacao` | Situação final | texto | "Finalizada avaliada" ou "Finalizada não avaliada" | ok |
| `avaliacao_reclamacao` | Avaliação do consumidor sobre a resolução | texto | "Resolvida", "Não Resolvida" ou "Não Avaliada" | ok |
| `nota_do_consumidor` | Nota de satisfação dada pelo consumidor | número | Nulo (~69%) quando não avaliada; 1 a 5 | ok |