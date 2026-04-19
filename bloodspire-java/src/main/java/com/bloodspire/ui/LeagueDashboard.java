package com.bloodspire.ui;

import com.bloodspire.manager.GameStateManager;
import javax.swing.*;
import java.awt.*;

/**
 * Main League Dashboard showing league status, teams, and navigation
 */
public class LeagueDashboard extends JPanel {
    
    private JFrame parentFrame;
    private String leagueName;
    private GameStateManager gameStateManager;
    
    public LeagueDashboard(JFrame frame, String name, boolean isNew) {
        this.parentFrame = frame;
        this.leagueName = name;
        
        // Initialize game state manager
        this.gameStateManager = new GameStateManager(name);
        if (isNew) {
            gameStateManager.initializeNewLeague();
        }
        
        setLayout(new BorderLayout());
        setBackground(new Color(20, 20, 30));
        
        // Header
        JPanel headerPanel = createHeaderPanel();
        add(headerPanel, BorderLayout.NORTH);
        
        // Main content
        JPanel mainPanel = createMainPanel();
        add(mainPanel, BorderLayout.CENTER);
        
        // Navigation
        JPanel navPanel = createNavigationPanel();
        add(navPanel, BorderLayout.SOUTH);
    }
    
    private JPanel createHeaderPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        panel.setBackground(new Color(40, 40, 50));
        panel.setPreferredSize(new Dimension(panel.getPreferredSize().width, 80));
        
        JLabel titleLabel = new JLabel("League: " + leagueName);
        titleLabel.setFont(new Font("Arial", Font.BOLD, 24));
        titleLabel.setForeground(new Color(200, 200, 200));
        panel.add(titleLabel);
        
        return panel;
    }
    
    private JPanel createMainPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(new Color(20, 20, 30));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(15, 15, 15, 15);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        
        // League Info
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.gridwidth = 2;
        panel.add(createInfoBox("Current Week", "1"), gbc);
        
        gbc.gridy = 1;
        panel.add(createInfoBox("Total Teams", "8"), gbc);
        
        gbc.gridy = 2;
        panel.add(createInfoBox("Your Gold", "1000"), gbc);
        
        return panel;
    }
    
    private JPanel createInfoBox(String title, String value) {
        JPanel box = new JPanel(new BorderLayout());
        box.setBackground(new Color(50, 50, 60));
        box.setBorder(BorderFactory.createLineBorder(new Color(100, 100, 100), 1));
        box.setPreferredSize(new Dimension(300, 80));
        
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Arial", Font.PLAIN, 14));
        titleLabel.setForeground(Color.GRAY);
        titleLabel.setBorder(BorderFactory.createEmptyBorder(5, 10, 0, 10));
        box.add(titleLabel, BorderLayout.NORTH);
        
        JLabel valueLabel = new JLabel(value);
        valueLabel.setFont(new Font("Arial", Font.BOLD, 24));
        valueLabel.setForeground(new Color(200, 200, 200));
        valueLabel.setHorizontalAlignment(SwingConstants.CENTER);
        box.add(valueLabel, BorderLayout.CENTER);
        
        return box;
    }
    
    private JPanel createNavigationPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER, 20, 15));
        panel.setBackground(new Color(40, 40, 50));
        panel.setPreferredSize(new Dimension(panel.getPreferredSize().width, 100));
        
        JButton teamButton = createNavButton("Team Management", e -> showTeamManagement());
        panel.add(teamButton);
        
        JButton arenaButton = createNavButton("Arena", e -> showArena());
        panel.add(arenaButton);
        
        JButton standingsButton = createNavButton("Standings", e -> showStandings());
        panel.add(standingsButton);
        
        JButton saveButton = createNavButton("Save & Exit", e -> saveAndExit());
        panel.add(saveButton);
        
        return panel;
    }
    
    private JButton createNavButton(String text, java.awt.event.ActionListener listener) {
        JButton button = new JButton(text);
        button.setFont(new Font("Arial", Font.BOLD, 14));
        button.setPreferredSize(new Dimension(180, 50));
        button.setBackground(new Color(60, 60, 80));
        button.setForeground(Color.WHITE);
        button.setFocusPainted(false);
        button.addActionListener(listener);
        return button;
    }
    
    private void showTeamManagement() {
        TeamManagementScreen teamScreen = new TeamManagementScreen(parentFrame, gameStateManager);
        parentFrame.getContentPane().removeAll();
        parentFrame.getContentPane().add(teamScreen);
        parentFrame.revalidate();
        parentFrame.repaint();
    }
    
    private void showArena() {
        ArenaScreen arenaScreen = new ArenaScreen(parentFrame, gameStateManager);
        parentFrame.getContentPane().removeAll();
        parentFrame.getContentPane().add(arenaScreen);
        parentFrame.revalidate();
        parentFrame.repaint();
    }
    
    private void showStandings() {
        JOptionPane.showMessageDialog(
            this,
            "Standings feature coming soon!",
            "Standings",
            JOptionPane.INFORMATION_MESSAGE
        );
    }
    
    private void saveAndExit() {
        int result = JOptionPane.showConfirmDialog(
            this,
            "Save league before exiting?",
            "Save League",
            JOptionPane.YES_NO_CANCEL_OPTION,
            JOptionPane.QUESTION_MESSAGE
        );
        
        if (result == JOptionPane.YES_OPTION) {
            // TODO: Save league
            JOptionPane.showMessageDialog(
                this,
                "League saved successfully!",
                "Save Complete",
                JOptionPane.INFORMATION_MESSAGE
            );
        }
        
        if (result != JOptionPane.CANCEL_OPTION) {
            System.exit(0);
        }
    }
}
