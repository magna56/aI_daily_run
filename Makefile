# AI Daily Learn — the reader UI for the daily session artifacts, published to
# GitHub Pages and Cloudflare Pages.
#
# Each session is a YYYY-MM-DD/ folder written by the /ai-daily-learn skill.
# build.js compiles those folders into site/data/ (a small manifest plus one
# JSON payload per session, with diagrams pre-rendered to SVG and each
# code_example.py executed so its output can be read in the browser).
# `make site` assembles the publishable folder; deploy.sh pushes it to both
# gh-pages (GitHub Pages) and Cloudflare Pages.
#
# Set NORUN=1 on any target to skip executing the Python examples — handy when
# iterating on index.html, since a cold run of all sessions takes ~45s.

OUTPUT_DIR := site
PORT       := 8000

ifeq ($(NORUN),1)
BUILD_FLAGS := --no-run
endif

.PHONY: build check mix site serve deploy clean help

build: ## Regenerate site/data/ from the session folders
	node build.js $(BUILD_FLAGS)

check: ## Lint every session without writing anything (use in review/CI)
	node build.js --check

mix: ## What to publish next: trailing-10 audience mix, what's due, what to avoid
	@node build.js --mix

site: build ## Assemble the publishable site/ folder
	mkdir -p $(OUTPUT_DIR)
	# index.html is NOT copied — build.js generates it (with the crawlable
	# <noscript> index baked in), same as sitemap.xml and feed.xml. Copying it
	# here would clobber that, since this target runs after `build`.
	cp 404.html about.html privacy.html terms.html manifest.json robots.txt $(OUTPUT_DIR)/
	cp favicon.svg favicon-16.png favicon-32.png apple-touch-icon.png icon-192.png icon-512.png og-image.png $(OUTPUT_DIR)/
	cp -R functions $(OUTPUT_DIR)/
	@echo "note: functions/ (OAuth + newsletter) only run on Cloudflare Pages — GitHub Pages has no serverless functions; the signup form posts to theaicommit.com"
	touch $(OUTPUT_DIR)/.nojekyll
	printf '%s\n' '/api/*  /api/:splat  200' '/*  /index.html  200' > $(OUTPUT_DIR)/_redirects
	@echo "==> Built $(OUTPUT_DIR)/"

serve: site ## Preview locally at http://127.0.0.1:$(PORT) (Ctrl-C to stop)
	@echo "==> http://127.0.0.1:$(PORT)"
	cd $(OUTPUT_DIR) && python3 -m http.server $(PORT)

deploy: ## Build and publish the site to the gh-pages branch
	./deploy.sh

clean: ## Remove build output and the cached run results
	rm -rf $(OUTPUT_DIR) .build-cache.json

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'
