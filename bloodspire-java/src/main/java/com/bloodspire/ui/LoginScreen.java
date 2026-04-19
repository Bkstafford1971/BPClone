package com.bloodspire.ui;

import javax.swing.*;
import java.awt.*;
import java.io.File;

/**
 * Login/Startup Screen for creating or loading a league
 */
public class LoginScreen extends JPanel {
    
    private JFrame parentFrame;
    
    public LoginScreen(JFrame frame) {
        this.parentFrame = frame;
        setLayout(new GridBagLayout());
        setBackground(new Color(30, 30, 40));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(10, 10, 10, 10);
        
        // Title
        JLabel titleLabel = new JLabel("BLOODSPIRE ARENA");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 36));
        titleLabel.setForeground(new Color(200, 50, 50));
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.gridwidth = 2;
        add(titleLabel, gbc);
        
        // Subtitle
        JLabel subtitleLabel = new JLabel("The Ultimate Combat League");
        subtitleLabel.setFont(new Font("Arial", Font.PLAIN, 18));
        subtitleLabel.setForeground(Color.LIGHT_GRAY);
        gbc.gridy = 1;
        add(subtitleLabel, gbc);
        
        // New League Button
        JButton newLeagueButton = new JButton("Create New League");
        newLeagueButton.setFont(new Font("Arial", Font.BOLD, 16));
        newLeagueButton.setPreferredSize(new Dimension(250, 50));
        newLeagueButton.addActionListener(e -> createNewLeague());
        gbc.gridy = 2;
        gbc.gridwidth = 1;
        add(newLeagueButton, gbc);
        
        // Load League Button
        JButton loadLeagueButton = new JButton("Load Existing League");
        loadLeagueButton.setFont(new Font("Arial", Font.BOLD, 16));
        loadLeagueButton.setPreferredSize(new Dimension(250, 50));
        loadLeagueButton.addActionListener(e -> loadLeague());
        gbc.gridy = 3;
        add(loadLeagueButton, gbc);
        
        // Exit Button
        JButton exitButton = new JButton("Exit");
        exitButton.setFont(new Font("Arial", Font.BOLD, 16));
        exitButton.setPreferredSize(new Dimension(250, 50));
        exitButton.addActionListener(e -> System.exit(0));
        gbc.gridy = 4;
        add(exitButton, gbc);
    }
    
    private void createNewLeague() {
        String leagueName = JOptionPane.showInputDialog(
            this,
            "Enter League Name:",
            "New League",
            JOptionPane.QUESTION_MESSAGE
        );
        
        if (leagueName != null && !leagueName.trim().isEmpty()) {
            // Create new league and show dashboard
            LeagueDashboard dashboard = new LeagueDashboard(parentFrame, leagueName.trim(), true);
            parentFrame.getContentPane().removeAll();
            parentFrame.getContentPane().add(dashboard);
            parentFrame.revalidate();
            parentFrame.repaint();
        }
    }
    
    private void loadLeague() {
        JFileChooser fileChooser = new JFileChooser();
        fileChooser.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(
            "Bloodspire League Files", "json"
        ));
        fileChooser.setCurrentDirectory(new File(System.getProperty("user.home")));
        
        int result = fileChooser.showOpenDialog(this);
        if (result == JFileChooser.APPROVE_OPTION) {
            File selectedFile = fileChooser.getSelectedFile();
            // TODO: Load league from file
            JOptionPane.showMessageDialog(
                this,
                "Loading league: " + selectedFile.getName(),
                "Load League",
                JOptionPane.INFORMATION_MESSAGE
            );
            
            LeagueDashboard dashboard = new LeagueDashboard(parentFrame, selectedFile.getName(), false);
            parentFrame.getContentPane().removeAll();
            parentFrame.getContentPane().add(dashboard);
            parentFrame.revalidate();
            parentFrame.repaint();
        }
    }
}
