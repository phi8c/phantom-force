import { createSlice } from "@reduxjs/toolkit";

interface AppState {
  sidebarCollapsed: boolean;
}

const initialState: AppState = {
  sidebarCollapsed: false,
};

const appSlice = createSlice({
  name: "app",
  initialState,
  reducers: {
    toggleSidebar(state) {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed(state, action: { payload: boolean }) {
      state.sidebarCollapsed = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarCollapsed,
} = appSlice.actions;

export default appSlice.reducer;