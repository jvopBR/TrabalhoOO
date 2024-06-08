    // Função para excluir uma nota do banco de dados
    function deleteNote(noteId) {
        // Envia uma solicitação para o servidor para excluir a nota
        fetch("/delete-note", {
            method: "POST",
            // Envia o ID da nota a ser excluída como dados JSON na solicitação
            body: JSON.stringify({ noteId: noteId }),
        }).then((_res) => {
            // Redireciona para a página inicial após a exclusão bem-sucedida
            window.location.href = "/";
        });
    }

    // Função para habilitar a edição de uma nota
    function enableEdit(noteId) {
        // Obtém a área de texto da nota com base no ID da nota
        const noteTextarea = document.getElementById(`note-${noteId}`);
        // Habilita a área de texto para edição
        noteTextarea.disabled = false;
        // Exibe o botão de salvar após clicar no botão de edição
        document.getElementById(`save-${noteId}`).style.display = 'inline-block';
        // Esconde o botão de edição após clicar nele
        document.getElementById(`edit-${noteId}`).style.display = 'none';
    }

    // Função para editar uma nota no banco de dados
    function editNote(noteId) {
        // Obtém a nova data da nota da área de texto
        const noteTextarea = document.getElementById(`note-${noteId}`);
        const newNoteData = noteTextarea.value;
        // Verifica se há nova data para editar
        if (newNoteData) {
            // Envia uma solicitação para o servidor para editar a nota
            fetch('/update-note', {
                method: 'POST',
                // Envia o ID da nota e a nova data como dados JSON na solicitação
                body: JSON.stringify({ noteId: noteId, newData: newNoteData }),
            }).then((_res) => {
                // Redireciona para a página inicial após a edição bem-sucedida
                window.location.href = "/";
            });
        }
    }

    // Função assíncrona para enviar mensagem para o ChatGPT
    async function sendMessage() {
        // Obtém a mensagem do usuário do campo de entrada
        const userMessage = document.getElementById('user-message').value;
        // Obtém a área de resposta onde a resposta do ChatGPT será exibida
        const responseArea = document.getElementById('response-area');

        // Verifica se a mensagem do usuário não está vazia
        if (userMessage) {
            try {
                // Envia uma solicitação assíncrona para o servidor para processar a mensagem do usuário
                const response = await fetch("/chat", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    // Envia a mensagem do usuário como dados JSON na solicitação
                    body: JSON.stringify({ message: userMessage })
                });

                // Analisa a resposta JSON retornada pelo servidor
                const data = await response.json();
                // Verifica se a resposta do ChatGPT está disponível
                if (data.reply) {
                    // Exibe a mensagem do usuário e a resposta do ChatGPT na área de resposta
                    responseArea.innerHTML = `<p><strong>You:</strong> ${userMessage}</p><p><strong>ChatGPT:</strong> ${data.reply}</p>`;
                } else {
                    // Exibe uma mensagem de erro caso não haja resposta do ChatGPT
                    responseArea.innerHTML = `<p><strong>ChatGPT:</strong> Ocorreu um erro ao processar sua solicitação.</p>`;
                }
            } catch (error) {
                // Exibe uma mensagem de erro em caso de falha ao enviar a mensagem
                console.error("Erro ao enviar mensagem:", error);
                responseArea.innerHTML = `<p><strong>Erro:</strong> Ocorreu um erro ao enviar a mensagem.</p>`;
            }
        }
    }
