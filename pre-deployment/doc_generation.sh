# Update licenseheaders
uv run python -m licenseheaders -t pre-deployment/gpl-affero-v3.tmpl -y 2026 -o "Pertti Palo" -n "Fictional Map Maker" -u https://github.com/giuthas-hobbies/fictional-map-maker/  --exclude docs/* .pixi/* .idea/* .vscode/* .VSCodeCounter/* *.html *.md *.markdown *.js *.xml *.yaml -v -v -v

# Generate docs with pdoc ...
uv run pre-deployment/generate_api_docs.py

# and some diagrams to be linked as well.
# Needs Graphviz to work properly
uvx --from pylint pyreverse -o png -p fimama -d docs/api src/fimama