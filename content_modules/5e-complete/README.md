# 5e Complete — módulo de conteúdo

Este diretório preserva o módulo Foundry VTT original do repositório
[ObsidimanWizard/5e-complete-V11](https://github.com/ObsidimanWizard/5e-complete-V11)
e seus compêndios separados.

Para importar o conteúdo navegável no compêndio web:

```bash
python backend/manage.py import_foundry_module content_modules/5e-complete \
  --slug 5e-complete --name "5e Complete Compendium" --module-version 0.3.3
```

O comando cria o módulo isolado `/modules/5e-complete`. Os packs de criaturas,
macros e tabelas continuam preservados no diretório original, mas não são
importados como páginas porque o compêndio web não possui esses tipos.
