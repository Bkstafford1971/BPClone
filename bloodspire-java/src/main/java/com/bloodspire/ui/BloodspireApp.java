package com.bloodspire.ui;

import com.bloodspire.manager.GameStateManager;
import com.bloodspire.model.*;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;

/**
 * Main desktop application window for Bloodspire.
 * Replaces the HTML client with a native Java Swing interface.
 */
public class BloodspireApp extends JFrame {
    
    private CardLayout cardLayout;
    private JPanel mainPanel;
    private GameStateManager gameStateManager;
    
    // Screens
    private LoginScreen loginScreen;
    private LeagueDashboard dashboard;
    private TeamManagementScreen teamScreen;
    private ArenaScreen arenaScreen;
    
    public BloodspireApp() {
        super("BLOODSPIRE - Arena Combat League");
        
        gameStateManager = new GameStateManager();
        
        initializeUI();
        
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1200, 800);
        setLocationRelativeTo(null);
        setVisible(true);
    }
    
    private void initializeUI() {
        cardLayout = new CardLayout();
        mainPanel = new JPanel(cardLayout);
        
        // Create screens
        loginScreen = new LoginScreen(this);
        dashboard = new LeagueDashboard(this, gameStateManager);
        teamScreen = new TeamManagementScreen(this, gameStateManager);
        arenaScreen = new ArenaScreen(this, gameStateManager);
        
        // Add screens to card layout
        mainPanel.add(loginScreen, "LOGIN");
        mainPanel.add(dashboard, "DASHBOARD");
        mainPanel.add(teamScreen, "TEAM");
        mainPanel.add(arenaScreen, "ARENA");
        
        add(mainPanel);
    }
    
    /**
     * Navigate to a specific screen
     */
    public void showScreen(String screenName) {
        cardLayout.show(mainPanel, screenName);
    }
    
    /**
     * Get the game state manager
     */
    public GameStateManager getGameStateManager() {
        return gameStateManager;
    }
    
    /**
     * Update UI after game state changes
     */
    public void refreshUI() {
        dashboard.refresh();
        teamScreen.refresh();
        arenaScreen.refresh();
    }
    
    /**
     * Main entry point
     */
    public static void main(String[] args) {
        // Set system look and feel
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        SwingUtilities.invokeLater(() -> new BloodspireApp());
    }
}
