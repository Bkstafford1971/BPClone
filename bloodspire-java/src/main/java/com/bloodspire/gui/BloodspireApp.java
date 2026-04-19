package com.bloodspire.gui;

import com.bloodspire.ui.LoginScreen;
import javax.swing.*;
import java.awt.*;

/**
 * Main entry point for the Bloodspire Desktop Application
 */
public class BloodspireApp {
    
    public static void main(String[] args) {
        // Set look and feel to system default
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        // Run on EDT
        SwingUtilities.invokeLater(() -> {
            JFrame frame = new JFrame("BLOODSPIRE ARENA");
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setSize(1200, 800);
            frame.setLocationRelativeTo(null);
            
            // Start with login screen
            LoginScreen loginScreen = new LoginScreen(frame);
            frame.getContentPane().add(loginScreen);
            
            frame.setVisible(true);
        });
    }
}
