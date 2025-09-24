import { clearMessagesFromStorage } from "./storageMessages";

function handleLogout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    clearMessagesFromStorage();
    window.location.href = '/';
};


export default handleLogout;

