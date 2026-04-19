package com.bloodspire.ui;

import com.bloodspire.manager.GameStateManager;
import com.bloodspire.model.Warrior;
import com.bloodspire.model.Team;
import javax.swing.*;
import java.awt.*;
import java.util.List;

/**
 * Team Management Screen for viewing roster, equipment, training, and free agents
 */
public class TeamManagementScreen extends JPanel {
    
    private JFrame parentFrame;
    private GameStateManager gameStateManager;
    private JTabbedPane tabbedPane;
    
    public TeamManagementScreen(JFrame frame, GameStateManager manager) {
        this.parentFrame = frame;
        this.gameStateManager = manager;
        
        setLayout(new BorderLayout());
        setBackground(new Color(20, 20, 30));
        
        // Header
        JPanel headerPanel = createHeaderPanel();
        add(headerPanel, BorderLayout.NORTH);
        
        // Tabbed pane for different sections
        tabbedPane = new JTabbedPane();
        tabbedPane.setBackground(new Color(40, 40, 50));
        tabbedPane.setForeground(Color.WHITE);
        tabbedPane.setFont(new Font("Arial", Font.BOLD, 14));
        
        // Roster Tab
        tabbedPane.addTab("Roster", createRosterPanel());
        
        // Free Agents Tab
        tabbedPane.addTab("Free Agents", createFreeAgentsPanel());
        
        // Training Tab
        tabbedPane.addTab("Training", createTrainingPanel());
        
        add(tabbedPane, BorderLayout.CENTER);
        
        // Back button
        JPanel backPanel = createBackPanel();
        add(backPanel, BorderLayout.SOUTH);
    }
    
    private JPanel createHeaderPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        panel.setBackground(new Color(40, 40, 50));
        panel.setPreferredSize(new Dimension(panel.getPreferredSize().width, 60));
        
        JLabel titleLabel = new JLabel("Team Management");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 20));
        titleLabel.setForeground(new Color(200, 200, 200));
        panel.add(titleLabel);
        
        return panel;
    }
    
    private JPanel createRosterPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(new Color(20, 20, 30));
        
        // Fighter list
        DefaultListModel<String> listModel = new DefaultListModel<>();
        List<Warrior> roster = gameStateManager.getPlayerTeam().getFighters();
        
        if (roster.isEmpty()) {
            listModel.addElement("No fighters in roster. Visit Free Agents to hire!");
        } else {
            for (Warrior w : roster) {
                listModel.addElement(w.getName() + " - " + w.getRace() + " " + w.getPrimaryStyle());
            }
        }
        
        JList<String> fighterList = new JList<>(listModel);
        fighterList.setFont(new Font("Arial", Font.PLAIN, 14));
        fighterList.setBackground(new Color(30, 30, 40));
        fighterList.setForeground(Color.WHITE);
        fighterList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        
        JScrollPane scrollPane = new JScrollPane(fighterList);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(100, 100, 100), 1));
        panel.add(scrollPane, BorderLayout.CENTER);
        
        // Fighter details panel
        JPanel detailsPanel = createFighterDetailsPanel();
        panel.add(detailsPanel, BorderLayout.EAST);
        
        return panel;
    }
    
    private JPanel createFighterDetailsPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(new Color(40, 40, 50));
        panel.setPreferredSize(new Dimension(350, 0));
        panel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(100, 100, 100)),
            "Fighter Details",
            0,
            0,
            new Font("Arial", Font.BOLD, 14),
            Color.WHITE
        ));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 10, 5, 10);
        gbc.anchor = GridBagConstraints.WEST;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        
        gbc.gridx = 0;
        gbc.gridy = 0;
        panel.add(createDetailLabel("Name:"), gbc);
        gbc.gridx = 1;
        panel.add(createDetailValue("Select a fighter"), gbc);
        
        gbc.gridx = 0;
        gbc.gridy = 1;
        panel.add(createDetailLabel("Race:"), gbc);
        gbc.gridx = 1;
        panel.add(createDetailValue("-"), gbc);
        
        gbc.gridx = 0;
        gbc.gridy = 2;
        panel.add(createDetailLabel("Style:"), gbc);
        gbc.gridx = 1;
        panel.add(createDetailValue("-"), gbc);
        
        gbc.gridx = 0;
        gbc.gridy = 3;
        panel.add(createDetailLabel("Health:"), gbc);
        gbc.gridx = 1;
        panel.add(createDetailValue("-"), gbc);
        
        gbc.gridx = 0;
        gbc.gridy = 4;
        panel.add(createDetailLabel("Stamina:"), gbc);
        gbc.gridx = 1;
        panel.add(createDetailValue("-"), gbc);
        
        // Equipment section
        gbc.gridx = 0;
        gbc.gridy = 5;
        gbc.gridwidth = 2;
        JLabel equipLabel = new JLabel("Equipment:");
        equipLabel.setFont(new Font("Arial", Font.BOLD, 12));
        equipLabel.setForeground(new Color(200, 200, 100));
        panel.add(equipLabel, gbc);
        
        gbc.gridy = 6;
        panel.add(createDetailValue("Weapon: None"), gbc);
        
        gbc.gridy = 7;
        panel.add(createDetailValue("Armor: None"), gbc);
        
        return panel;
    }
    
    private JLabel createDetailLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(new Font("Arial", Font.BOLD, 12));
        label.setForeground(new Color(200, 200, 200));
        return label;
    }
    
    private JLabel createDetailValue(String text) {
        JLabel label = new JLabel(text);
        label.setFont(new Font("Arial", Font.PLAIN, 12));
        label.setForeground(Color.WHITE);
        return label;
    }
    
    private JPanel createFreeAgentsPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(new Color(20, 20, 30));
        
        JLabel infoLabel = new JLabel("Available Free Agents (Click to Hire)");
        infoLabel.setFont(new Font("Arial", Font.BOLD, 16));
        infoLabel.setForeground(Color.WHITE);
        infoLabel.setHorizontalAlignment(SwingConstants.CENTER);
        panel.add(infoLabel, BorderLayout.NORTH);
        
        // Free agent list
        DefaultListModel<String> listModel = new DefaultListModel<>();
        listModel.addElement("Grom - Orc Brawler (50 gold)");
        listModel.addElement("Swift - Elf Duelist (75 gold)");
        listModel.addElement("Thorgar - Dwarf Guardian (60 gold)");
        listModel.addElement("Zara - Human Berserker (45 gold)");
        
        JList<String> agentList = new JList<>(listModel);
        agentList.setFont(new Font("Arial", Font.PLAIN, 14));
        agentList.setBackground(new Color(30, 30, 40));
        agentList.setForeground(Color.WHITE);
        
        JScrollPane scrollPane = new JScrollPane(agentList);
        scrollPane.setBorder(BorderFactory.createLineBorder(new Color(100, 100, 100), 1));
        panel.add(scrollPane, BorderLayout.CENTER);
        
        // Hire button
        JButton hireButton = new JButton("Hire Selected Fighter");
        hireButton.setFont(new Font("Arial", Font.BOLD, 14));
        hireButton.setPreferredSize(new Dimension(200, 40));
        hireButton.addActionListener(e -> {
            int selectedIndex = agentList.getSelectedIndex();
            if (selectedIndex >= 0) {
                JOptionPane.showMessageDialog(
                    this,
                    "Fighter hired successfully!",
                    "Hire Fighter",
                    JOptionPane.INFORMATION_MESSAGE
                );
            } else {
                JOptionPane.showMessageDialog(
                    this,
                    "Please select a fighter to hire.",
                    "No Selection",
                    JOptionPane.WARNING_MESSAGE
                );
            }
        });
        
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER));
        buttonPanel.setBackground(new Color(20, 20, 30));
        buttonPanel.add(hireButton);
        panel.add(buttonPanel, BorderLayout.SOUTH);
        
        return panel;
    }
    
    private JPanel createTrainingPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(new Color(20, 20, 30));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(10, 10, 10, 10);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        
        gbc.gridx = 0;
        gbc.gridy = 0;
        panel.add(createTrainingOption("Train Strength", "50 gold"), gbc);
        
        gbc.gridy = 1;
        panel.add(createTrainingOption("Train Agility", "50 gold"), gbc);
        
        gbc.gridy = 2;
        panel.add(createTrainingOption("Train Tactics", "50 gold"), gbc);
        
        gbc.gridy = 3;
        panel.add(createTrainingOption("Train Endurance", "50 gold"), gbc);
        
        gbc.gridy = 4;
        panel.add(createTrainingOption("Practice Fighting", "30 gold"), gbc);
        
        return panel;
    }
    
    private JPanel createTrainingOption(String name, String cost) {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        panel.setBackground(new Color(40, 40, 50));
        panel.setBorder(BorderFactory.createLineBorder(new Color(100, 100, 100), 1));
        panel.setPreferredSize(new Dimension(400, 60));
        
        JLabel nameLabel = new JLabel(name);
        nameLabel.setFont(new Font("Arial", Font.BOLD, 14));
        nameLabel.setForeground(Color.WHITE);
        panel.add(nameLabel);
        
        JLabel costLabel = new JLabel(cost);
        costLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        costLabel.setForeground(new Color(200, 200, 100));
        panel.add(costLabel);
        
        JButton trainButton = new JButton("Train");
        trainButton.setFont(new Font("Arial", Font.BOLD, 12));
        trainButton.setPreferredSize(new Dimension(100, 30));
        trainButton.addActionListener(e -> {
            JOptionPane.showMessageDialog(
                this,
                "Training complete!",
                "Training",
                JOptionPane.INFORMATION_MESSAGE
            );
        });
        panel.add(trainButton);
        
        return panel;
    }
    
    private JPanel createBackPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER));
        panel.setBackground(new Color(40, 40, 50));
        panel.setPreferredSize(new Dimension(panel.getPreferredSize().width, 70));
        
        JButton backButton = new JButton("Back to Dashboard");
        backButton.setFont(new Font("Arial", Font.BOLD, 14));
        backButton.setPreferredSize(new Dimension(200, 40));
        backButton.addActionListener(e -> {
            LeagueDashboard dashboard = new LeagueDashboard(parentFrame, "League", false);
            parentFrame.getContentPane().removeAll();
            parentFrame.getContentPane().add(dashboard);
            parentFrame.revalidate();
            parentFrame.repaint();
        });
        panel.add(backButton);
        
        return panel;
    }
}
