import handleLogout from "./userLogout";

function checkToken() {
      const token = localStorage.getItem('authToken');
      const storedUserData = localStorage.getItem('userData');

      if (!token || !storedUserData) {
        handleLogout();
        return null;
      }

      return JSON.parse(storedUserData);
}

export default checkToken;
