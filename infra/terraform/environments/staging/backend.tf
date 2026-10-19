# Structural placeholder: initialize only after authorized infra-bootstrap.
# Implement backend "azurerm"; nonsecret selectors live in backend.hcl.
# Entra data-plane authorization, OIDC in CI and native Blob-lease locking.
# Use a dedicated protected account/container and a separate staging state key.
