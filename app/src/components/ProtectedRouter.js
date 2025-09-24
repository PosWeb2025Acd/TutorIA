import { Outlet } from "react-router-dom";
import handleLogout from "../functions/userLogout";

function ProtectedRoute() {
    const userToken = localStorage.getItem('authToken');
    const userIsLogged = userToken !== null && userToken !== undefined && userToken !== ''
    if (userIsLogged) {
        return <Outlet />
    }

    handleLogout();
}

export default ProtectedRoute
