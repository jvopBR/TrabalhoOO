function deleteNote(noteId) {
    fetch("/delete-note", {
        method: "POST",
        body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
        window.location.href = "/";
    });
}

function enableEdit(noteId) {
    const noteTextarea = document.getElementById(`note-${noteId}`);
    noteTextarea.disabled = false;
    document.getElementById(`save-${noteId}`).style.display = 'inline-block';
    document.getElementById(`edit-${noteId}`).style.display = 'none';
}

function editNote(noteId) {
    const noteTextarea = document.getElementById(`note-${noteId}`);
    const newNoteData = noteTextarea.value;
    if (newNoteData) {
        fetch('/update-note', {
            method: 'POST',
            body: JSON.stringify({ noteId: noteId, newData: newNoteData }),
        }).then((_res) => {
            window.location.href = "/";
        });
    }
}

async function sendMessage() {
    const userMessage = document.getElementById('user-message').value;
    const responseArea = document.getElementById('response-area');

    if (userMessage) {
        try {
            const response = await fetch("/chat", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userMessage })
            });

            const data = await response.json();
            if (data.reply) {
                responseArea.innerHTML = `<p><strong>You:</strong> ${userMessage}</p><p><strong>ChatGPT:</strong> ${data.reply}</p>`;
            } else {
                responseArea.innerHTML = `<p><strong>ChatGPT:</strong> Ocorreu um erro ao processar sua solicitação.</p>`;
            }
        } catch (error) {
            console.error("Erro ao enviar mensagem:", error);
            responseArea.innerHTML = `<p><strong>Erro:</strong> Ocorreu um erro ao enviar a mensagem.</p>`;
        }
    }
}