#!/usr/bin/env bash
set -e

# ExpressDefault Profile
# Creates a basic Express.js web application

PARENT_DIR="$1"
PROJECT_NAME="$2"
PROJECT_PATH="${PARENT_DIR}/${PROJECT_NAME}"

# Create project directory
mkdir -p "${PROJECT_PATH}"
cd "${PROJECT_PATH}"

# Initialize npm project
npm init -y

# Install Express
npm install express

# Create basic server file
cat > index.js << 'EOF'
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send('Hello World!');
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
node_modules/
.env
*.log
EOF

# Create README
cat > README.md << EOF
# ${PROJECT_NAME}

A basic Express.js application.

## Installation

\`\`\`bash
npm install
\`\`\`

## Usage

\`\`\`bash
node index.js
\`\`\`

Then visit http://localhost:3000
EOF

echo "Express.js project created successfully!"
