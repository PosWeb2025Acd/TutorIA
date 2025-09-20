function handleLogout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    window.location.href = '/';
};


export default handleLogout;

