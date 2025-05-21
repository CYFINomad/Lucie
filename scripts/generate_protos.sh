#!/bin/bash

# Script to generate Protocol Buffer code for Node.js and Python
# This script should be run from the project root directory

# Set variables
PROTO_DIR="./shared/protos"
NODE_OUTPUT_DIR="./backend/python-bridge/protos"
PYTHON_OUTPUT_DIR="./python-ai/grpc/protos"

# Create output directories if they don't exist
mkdir -p "$NODE_OUTPUT_DIR"
mkdir -p "$PYTHON_OUTPUT_DIR"

# Install required tools if not installed
check_and_install() {
    if ! command -v $1 &> /dev/null; then
        echo "$1 is not installed. Installing..."
        if [[ "$1" == "protoc" ]]; then
            # Install protoc (Protocol Buffer compiler)
            # This is a simplified example - actual installation may vary by OS
            apt-get update && apt-get install -y protobuf-compiler
        elif [[ "$1" == "grpc_tools_node_protoc" ]]; then
            # Install gRPC tools for Node.js
            npm install -g grpc-tools
        fi
    fi
}

check_and_install "protoc"
check_and_install "grpc_tools_node_protoc"

# Generate JavaScript/TypeScript code
echo "Generating Node.js protobuf code..."
grpc_tools_node_protoc \
    --js_out=import_style=commonjs,binary:$NODE_OUTPUT_DIR \
    --grpc_out=grpc_js:$NODE_OUTPUT_DIR \
    --proto_path=$PROTO_DIR \
    $PROTO_DIR/*.proto

# Generate Python code
echo "Generating Python protobuf code..."
python -m grpc_tools.protoc \
    --python_out=$PYTHON_OUTPUT_DIR \
    --grpc_python_out=$PYTHON_OUTPUT_DIR \
    --proto_path=$PROTO_DIR \
    $PROTO_DIR/*.proto

echo "Protocol buffer code generation complete!"

# Fix Python imports
# Python generates files with relative imports that may not work correctly
echo "Fixing Python imports..."
PYTHON_FILES="$PYTHON_OUTPUT_DIR/*.py"
for file in $PYTHON_FILES; do
    # Replace relative imports with absolute imports
    sed -i 's/^import \([a-zA-Z0-9_]*\)_pb2/from . import \1_pb2/g' "$file"
    sed -i 's/^import \([a-zA-Z0-9_]*\)_pb2_grpc/from . import \1_pb2_grpc/g' "$file"
done

echo "All done! Generated files are in $NODE_OUTPUT_DIR and $PYTHON_OUTPUT_DIR" 