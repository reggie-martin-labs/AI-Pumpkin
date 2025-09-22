#!/usr/bin/env node
"use strict";
/**
 * generate.js
 * Simple scaffold to generate assets using Azure OpenAI Images.
 * Usage:
 *   node generate.js head [--force]
 *   node generate.js mouths [--force]
 *
 * This script uses environment variables:
 * - AZURE_OPENAI_ENDPOINT
 * - AZURE_OPENAI_KEY
 * - AZURE_OPENAI_IMAGES_DEPLOYMENT
 *
 * It will write files under ./assets/. It will NOT run unless you explicitly
 * call it. This scaffold uses the @azure/openai client.
 */

const fs = require('fs');
const path = require('path');
const process = require('process');

const ASSETS_DIR = path.resolve(__dirname, 'assets');
if (!fs.existsSync(ASSETS_DIR)) fs.mkdirSync(ASSETS_DIR, { recursive: true });

const HEAD_NAME = 'plate_head.png';
const MOUTH_NAMES = [
  'mouth_closed', 'mouth_wide', 'mouth_o', 'mouth_ee', 'mouth_ah',
  'mouth_oh', 'mouth_fv', 'mouth_th', 'mouth_smile', 'mouth_smirk'
];

function usage() {
  console.log('Usage: node generate.js <head|mouths> [--force]');
}

async function generateHead(force) {
  const out = path.join(ASSETS_DIR, HEAD_NAME);
  if (fs.existsSync(out) && !force) {
    console.log(out, 'already exists — run with --force to overwrite');
    return;
  }
  console.log('Ready to generate head at', out);
  console.log('This will call Azure OpenAI Images when you run it.');
  // Implementation note: the real call is below but commented out until you opt-in.

  /*
  // Uncomment and install @azure/openai to run
  const { OpenAIClient, AzureKeyCredential } = require('@azure/openai');
  const endpoint = process.env.AZURE_OPENAI_ENDPOINT;
  const key = process.env.AZURE_OPENAI_KEY;
  const deployment = process.env.AZURE_OPENAI_IMAGES_DEPLOYMENT || 'gpt-image-1';
  if (!endpoint || !key) throw new Error('Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY');
  const client = new OpenAIClient(endpoint, new AzureKeyCredential(key));

  const prompt = `Tim Burton–style jack-o-lantern, asymmetrical carved face, glowing from within, gothic charcoal background, stitched carved features, film grain, high contrast rim light, spooky but playful. Centered, single subject, no text. The pumpkin should have an empty carved mouth opening (no teeth or baked-in expression), designed to let separate mouth sprites overlay cleanly.`;

  const result = await client.generateImage({ prompt, size: '2048x2048', deployment });
  // save result to out (result contains base64 or URL depending on SDK)
  */
}

async function generateMouths(force) {
  for (const name of MOUTH_NAMES) {
    const out = path.join(ASSETS_DIR, `${name}.png`);
    if (fs.existsSync(out) && !force) {
      console.log(out, 'exists — skipping (use --force to overwrite)');
      continue;
    }
    console.log('Ready to generate mouth sprite at', out);

    /*
    // Example prompt (replace <shape> with shape name mapping as desired)
    const prompt = `Tim Burton–style carved jack-o-lantern mouth sprite (${name.replace('mouth_', '')}), glowing from within, carved wood/pumpkin texture with rim lighting, spooky but playful. Transparent background. Isolated carved mouth shape only (no pumpkin head). High contrast, Burton aesthetic.`;
    // Call Azure Images API similarly to the head example and write PNG to out.
    */
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) return usage();
  const cmd = args[0];
  const force = args.includes('--force');

  if (cmd === 'head') {
    await generateHead(force);
  } else if (cmd === 'mouths') {
    await generateMouths(force);
  } else {
    usage();
    process.exit(1);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
