package com.bloodspire.ui;

import com.bloodspire.manager.GameStateManager;
import javax.swing.*;
import java.awt.*;

/**
 * Login/Startup screen for creating or loading a league.
 */
public class LoginScreen extends JPanel {
    
    private BloodspireApp app;
    
    public LoginScreen(BloodspireApp app) {
        this.app = app;
        initializeUI();
    }
    
    private void initializeUI() {
        setLayout(new GridBagLayout());
        setBackground(new Color(30, 30, 40));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(10, 10, 10, 10);
        
        // Title
        JLabel titleLabel = new JLabel("BLOODSPIRE");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 48));
        titleLabel.setForeground(new Color(200, 50, 50));
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.gridwidth = 2;
        gbc.anchor = GridBagConstraints.CENTER;
        add(titleLabel, gbc);
        
        // Subtitle
        JLabel subtitleLabel = new JLabel("Arena Combat League");
        subtitleLabel.setFont(new Font("Arial", Font.PLAIN, 18));
        subtitleLabel.setForeground(Color.LIGHT_GRAY);
        gbc.gridy = 1;
        add(subtitleLabel, gbc);
        
        // Create New League Button
        JButton createButton = new JButton("Create New League");
        createButton.setFont(new Font("Arial", Font.BOLD, 16));
        createButton.setPreferredSize(new Dimension(250, 50));
        createButton.addActionListener(e -> {
            JDialog dialog = createLeagueDialog();
            dialog.setVisible(true);
        });
        gbc.gridy = 2;
        gbc.gridwidth = 1;
        add(createButton, gbc);
        
        // Load League Button
        JButton loadButton = new JButton("Load Existing League");
        loadButton.setFont(new Font("Arial", Font.BOLD, 16));
        loadButton.setPreferredSize(new Dimension(250, 50));
        loadButton.addActionListener(e -> {
            JFileChooser fileChooser = new JFileChooser();
            if (fileChooser.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
                try {
                    app.getGameStateManager().loadLeague(fileChooser.getSelectedFile().getAbsolutePath());
                    app.showScreen("DASHBOARD");
                } catch (Exception ex) {
                    JOptionPane.showMessageDialog(this, 
                        "Error loading league: " + ex.getMessage(),
                        "Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        });
        gbc.gridy = 3;
        add(loadButton, gbc);
        
        // Exit Button
        JButton exitButton = new JButton("Exit");
        exitButton.setFont(new Font("Arial", Font.BOLD, 16));
        exitButton.setPreferredSize(new Dimension(250, 50));
        exitButton.addActionListener(e -> System.exit(0));
        gbc.gridy = 4;
        add(exitButton, gbc);
    }
    
    private JDialog createLeagueDialog() {
        JDialog dialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(this), "Create New League", true);
        dialog.setLayout(new GridLayout(4, 2, 10, 10));
        dialog.setSize(400, 200);
        dialog.setLocationRelativeTo(this);
        
        // League Name
        dialog.add(new JLabel("League Name:"));
        JTextField nameField = new JTextField("Bloodspire League");
        dialog.add(nameField);
        
        // Number of Teams
        dialog.add(new JLabel("Number of Teams:"));
        JComboBox<Integer> teamCountCombo = new JComboBox<>(new Integer[]{4, 6, 8});
        teamCountCombo.setSelectedIndex(1); // Default 6
        dialog.add(teamCountCombo);
        
        // Buttons
        JPanel buttonPanel = new JPanel();
        JButton createBtn = new JButton("Create");
        JButton cancelBtn = new JButton("Cancel");
        
        createBtn.addActionListener(e -> {
            String name = nameField.getText().trim();
            int numTeams = (Integer) teamCountCombo.getSelectedItem();
            
            if (name.isEmpty()) {
                JOptionPane.showMessageDialog(dialog, "Please enter a league name", "Error", JOptionPane.ERROR_MESSAGE);
                return;
            }
            
            try {
                app.getGameStateManager().createLeague(name, numTeams);
                app.showScreen("DASHBOARD");
                dialog.dispose();
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(dialog, 
                    "Error creating league: " + ex.getMessage(),
                    "Error", JOptionPane.ERROR_MESSAGE);
            }
        });
        
        cancelBtn.addActionListener(e -> dialog.dispose());
        
        buttonPanel.add(createBtn);
        buttonPanel.add(cancelBtn);
        
        dialog.add(new JLabel()); // Empty cell
        dialog.add(buttonPanel);
        
        return dialog;
    }
}
