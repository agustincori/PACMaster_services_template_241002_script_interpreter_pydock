// Function to convert YAML to JSON
function yamlToJson(yaml) {
    try {
        return jsyaml.load(yaml);
    } catch (e) {
        console.error('Error parsing YAML:', e);
        return {};
    }
}

// Function to convert JSON to YAML
function jsonToYaml(json) {
    try {
        return jsyaml.dump(json);
    } catch (e) {
        console.error('Error converting JSON to YAML:', e);
        return '';
    }
}

function updatePayloadFormat(route) {
    const format = document.getElementById(`format_${route}`).value;
    const payloadTextarea = document.getElementById(`jsonPayload_${route}`);
    const currentPayload = payloadTextarea.value.trim();

    if (format === 'yaml') {
        try {
            const jsonData = JSON.parse(currentPayload);
            payloadTextarea.value = jsonToYaml(jsonData);
        } catch (e) {
            console.error('Failed to convert JSON to YAML:', e);
        }
    } else {
        try {
            const yamlData = yamlToJson(currentPayload);
            payloadTextarea.value = JSON.stringify(yamlData, null, 2);
        } catch (e) {
            console.error('Failed to convert YAML to JSON:', e);
        }
    }
}

function executePost(route) {
    const url = `/${route}`;
    const format = document.getElementById(`format_${route}`).value;
    const dataText = document.getElementById(`jsonPayload_${route}`).value;
    let data, contentType;

    if (format === 'yaml') {
        data = yamlToJson(dataText);
        contentType = 'application/x-yaml';
    } else {
        data = JSON.parse(dataText);
        contentType = 'application/json';
    }

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': contentType,
        },
        body: format === 'yaml' ? jsyaml.dump(data) : JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        document.getElementById(`resultBox_${route}`).value = JSON.stringify(result, null, 2);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById(`resultBox_${route}`).value = 'An error occurred: ' + error;
    });
}
