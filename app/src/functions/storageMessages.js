const MESSAGE_STORAGE_KEY = 'chatMessages';

function saveMessageOnStorage(messageObject) {
    const existingMessages = getAllMessageFromStorage();
    existingMessages.push(messageObject);
    localStorage.setItem(MESSAGE_STORAGE_KEY, JSON.stringify(existingMessages));
}

function getAllMessageFromStorage() {
    return JSON.parse(localStorage.getItem(MESSAGE_STORAGE_KEY)) || [];
}

function clearMessagesFromStorage() {
    localStorage.removeItem(MESSAGE_STORAGE_KEY);
}


export {
    saveMessageOnStorage,
    getAllMessageFromStorage,
    clearMessagesFromStorage,
}