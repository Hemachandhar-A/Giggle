import sys

files = [
    'frontend-new/src/pages/Register.jsx',
    'frontend-new/src/pages/Login.jsx',
    'frontend-new/src/pages/Demo.jsx',
    'frontend-new/src/pages/Admin.jsx',
    'frontend-new/src/pages/Landing.jsx',
    'frontend-new/src/components/Layout.jsx'
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace(' →', '')
    content = content.replace('→', '')
    content = content.replace('<span className="text-2xl">🛡️</span>\n', '')
    content = content.replace('<span>🛡️</span>', '')
    content = content.replace('🛡️', '')
    content = content.replace('⚡ ', '')
    content = content.replace('✓ Approve Mandate', 'Approve Mandate')
    content = content.replace('✓ Mark All Verified', 'Mark All Verified')
    content = content.replace('`${td.icon || \'🚨\'} ${t(\'demo.fire_trigger\')}`', 't(\'demo.fire_trigger\')')

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print('Done')
