const fs = require('fs');
const code = fs.readFileSync('C:/Users/86187/Desktop/yuyi_pro_v2/webapp/static/js/app.js', 'utf8');
try {
    new Function(code);
    console.log('SYNTAX OK');
} catch(e) {
    console.log('ERROR: ' + e.message);
    // Try to find problematic line by checking chunks
    const lines = code.split('\n');
    let lastGood = 0;
    for (let chunk = 100; chunk <= lines.length; chunk += 100) {
        try {
            new Function(lines.slice(0, chunk).join('\n'));
            lastGood = chunk;
        } catch(e2) {
            console.log('Error between lines ' + lastGood + '-' + chunk);
            // Narrow down
            for (let i = lastGood; i <= chunk; i++) {
                try {
                    new Function(lines.slice(0, i).join('\n'));
                } catch(e3) {
                    console.log('First error at line ' + i + ': ' + lines[i-1].substring(0, 100));
                    // Show context
                    for (let j = Math.max(0, i-3); j < Math.min(lines.length, i+2); j++) {
                        console.log((j+1) + ': ' + lines[j].substring(0, 120));
                    }
                    break;
                }
            }
            break;
        }
    }
}
