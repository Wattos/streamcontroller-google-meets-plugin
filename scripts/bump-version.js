#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Get the bump type from command line argument
const bumpType = process.argv[2] || 'patch';

if (!['major', 'minor', 'patch'].includes(bumpType)) {
  console.error('❌ Invalid bump type. Use: major, minor, or patch');
  process.exit(1);
}

// Function to bump version
function bumpVersion(version, type) {
  const [major, minor, patch] = version.split('.').map(Number);

  switch (type) {
    case 'major':
      return `${major + 1}.0.0`;
    case 'minor':
      return `${major}.${minor + 1}.0`;
    case 'patch':
      return `${major}.${minor}.${patch + 1}`;
    default:
      return version;
  }
}

// Paths to files that need version updates
const projectRoot = path.join(__dirname, '..');
const files = [
  {
    path: path.join(projectRoot, 'chrome_extension', 'manifest.json'),
    name: 'Chrome Extension manifest.json',
    type: 'extension'
  },
  {
    path: path.join(projectRoot, 'chrome_extension', 'package.json'),
    name: 'Chrome Extension package.json',
    type: 'extension'
  },
  {
    path: path.join(projectRoot, 'manifest.json'),
    name: 'StreamController Plugin manifest.json',
    type: 'plugin'
  }
];

console.log(`🔼 Bumping version (${bumpType})...\n`);
console.log('📋 Files to update:');
files.forEach(file => {
  console.log(`   - ${file.name}`);
});
console.log('');

// Read current version from first file
const firstFile = JSON.parse(fs.readFileSync(files[0].path, 'utf8'));
const oldVersion = firstFile.version;
const newVersion = bumpVersion(oldVersion, bumpType);

console.log(`📌 Version: ${oldVersion} → ${newVersion}\n`);

// Update all files
files.forEach(file => {
  try {
    const content = JSON.parse(fs.readFileSync(file.path, 'utf8'));
    content.version = newVersion;
    fs.writeFileSync(file.path, JSON.stringify(content, null, 2) + '\n');
    console.log(`✅ Updated: ${file.name}`);
  } catch (error) {
    console.error(`❌ Error updating ${file.name}:`, error.message);
    process.exit(1);
  }
});

console.log('\n✅ Version bump complete!');

// Verify all versions are in sync
console.log('\n🔍 Verifying version sync...');
const allInSync = files.every(file => {
  try {
    const content = JSON.parse(fs.readFileSync(file.path, 'utf8'));
    const inSync = content.version === newVersion;
    console.log(`   ${inSync ? '✅' : '❌'} ${file.name}: ${content.version}`);
    return inSync;
  } catch (error) {
    console.log(`   ❌ ${file.name}: Error reading file`);
    return false;
  }
});

if (!allInSync) {
  console.error('\n❌ Version sync failed! Not all files have matching versions.');
  process.exit(1);
}

console.log('\n✅ All versions synchronized to v' + newVersion);
console.log('\n📝 Next steps:');
console.log('   1. Review the changes');
console.log('   2. Commit: git add . && git commit -m "chore: bump version to v' + newVersion + '"');
console.log('   3. Create PR and merge to trigger automatic release');
