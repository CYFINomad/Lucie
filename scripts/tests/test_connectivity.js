#!/usr/bin/env node
/**
 * Test script to verify connectivity between Node.js backend and Python services
 */

const axios = require('axios');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../backend/.env') });

// Check if required environment variables are present
console.log('\n🔍 Checking environment variables...');
const requiredVars = ['PYTHON_API_URL', 'GRPC_SERVER'];
let missingVars = [];

requiredVars.forEach(varName => {
  if (!process.env[varName]) {
    missingVars.push(varName);
  } else {
    console.log(`✅ ${varName} = ${process.env[varName]}`);
  }
});

if (missingVars.length > 0) {
  console.error(`❌ Missing required environment variables: ${missingVars.join(', ')}`);
  console.error('   Please check your .env file in backend directory');
  process.exit(1);
}

// Test REST API
async function testRestAPI() {
  console.log('\n🔍 Testing REST API connection...');
  try {
    const url = `${process.env.PYTHON_API_URL}/health`;
    console.log(`   Connecting to ${url}`);
    
    const response = await axios.get(url, { timeout: 5000 });
    
    if (response.status === 200) {
      console.log('✅ REST API connection successful!');
      console.log(`   Status: ${response.data.status}`);
      console.log(`   Version: ${response.data.version}`);
      return true;
    } else {
      console.log(`❌ REST API returned non-200 status: ${response.status}`);
      return false;
    }
  } catch (error) {
    console.error('❌ Failed to connect to REST API:');
    if (error.code === 'ECONNREFUSED') {
      console.error(`   Connection refused. Is the Python API running at ${process.env.PYTHON_API_URL}?`);
    } else if (error.code === 'ETIMEDOUT') {
      console.error(`   Connection timed out. Is the Python API running at ${process.env.PYTHON_API_URL}?`);
    } else {
      console.error(`   ${error.message}`);
    }
    return false;
  }
}

// Test gRPC
async function testGRPC() {
  console.log('\n🔍 Testing gRPC connection...');
  
  const protoPath = path.join(__dirname, '../../shared/protos/lucie.proto');
  console.log(`   Using proto file: ${protoPath}`);
  console.log(`   Connecting to gRPC server: ${process.env.GRPC_SERVER}`);
  
  try {
    // Load proto file
    const packageDefinition = protoLoader.loadSync(protoPath, {
      keepCase: true,
      longs: String,
      enums: String,
      defaults: true,
      oneofs: true,
    });
    
    const proto = grpc.loadPackageDefinition(packageDefinition);
    
    // Create client
    const client = new proto.lucie.LucieService(
      process.env.GRPC_SERVER,
      grpc.credentials.createInsecure()
    );
    
    // Test connection
    return new Promise((resolve) => {
      const deadline = new Date();
      deadline.setSeconds(deadline.getSeconds() + 5);
      
      client.waitForReady(deadline, (error) => {
        if (error) {
          console.error('❌ gRPC connection failed:');
          console.error(`   ${error.message}`);
          resolve(false);
        } else {
          console.log('✅ gRPC connection successful!');
          
          // Test a simple method call
          console.log('\n   Testing gRPC method call...');
          const message = {
            content: 'Test message from Node.js backend',
            id: Date.now().toString(),
            user_id: 'test-user',
            session_id: 'test-session',
          };
          
          client.ProcessMessage(message, (err, response) => {
            if (err) {
              console.error(`❌ gRPC method call failed: ${err.message}`);
              resolve(false);
            } else {
              console.log('✅ gRPC method call successful!');
              console.log(`   Response: ${response.content}`);
              resolve(true);
            }
            
            // Close the client
            client.close();
          });
        }
      });
    });
  } catch (error) {
    console.error('❌ Failed to create gRPC client:');
    console.error(`   ${error.message}`);
    return false;
  }
}

// Main function
async function main() {
  console.log('🔍 Testing connectivity between Node.js and Python services\n');
  
  const restResult = await testRestAPI();
  const grpcResult = await testGRPC();
  
  console.log('\n📊 Results:');
  console.log(`   REST API: ${restResult ? '✅ Connected' : '❌ Failed'}`);
  console.log(`   gRPC: ${grpcResult ? '✅ Connected' : '❌ Failed'}`);
  
  if (restResult && grpcResult) {
    console.log('\n🎉 All services are connected and working!\n');
    process.exit(0);
  } else {
    console.log('\n⚠️ Some services are not connecting properly. Please check the logs above.\n');
    process.exit(1);
  }
}

// Run the main function
main().catch(error => {
  console.error('❌ Unexpected error:');
  console.error(error);
  process.exit(1);
}); 