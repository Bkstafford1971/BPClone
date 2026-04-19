package com.bloodspire.ui;

import com.bloodspire.manager.GameStateManager;
import com.bloodspire.model.*;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.util.List;

/**
 * Team management screen for viewing roster, equipment, training, and free agents.
 */
public class TeamManagementScreen extends JPanel {
    
    private BloodspireApp app;
    private GameStateManager gameStateManager;
    private JTable rosterTable;
    private DefaultTableModel rosterModel;
    private JTextArea fighterDetailsArea;
    private JComboBox<String> teamCombo;
    private JComboBox<String> statCombo;
    
    public TeamManagementScreen(BloodspireApp app, GameStateManager gameStateManager) {
        this.app = app;
        this.gameStateManager = gameStateManager;
        initializeUI();
    }
    
    private void initializeUI() {
        setLayout(new BorderLayout());
        setBackground(new Color(30, 30, 40));
        
        // Top panel with team selection and navigation
        JPanel topPanel = createTopPanel();
        add(topPanel, BorderLayout.NORTH);
        
        // Center split pane
        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        splitPane.setDividerLocation(600);
        
        // Left side - Roster table
        JPanel rosterPanel = createRosterPanel();
        splitPane.setLeftComponent(rosterPanel);
        
        // Right side - Fighter details and actions
        JPanel detailsPanel = createDetailsPanel();
        splitPane.setRightComponent(detailsPanel);
        
        add(splitPane, BorderLayout.CENTER);
        
        refresh();
    }
    
    private JPanel createTopPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        panel.setBackground(new Color(40, 40, 50));
        
        panel.add(new JLabel("Select Team:"));
        teamCombo = new JComboBox<>();
        teamCombo.addActionListener(e -> refreshRoster());
        panel.add(teamCombo);
        
        JButton backBtn = new JButton("Back to Dashboard");
        backBtn.addActionListener(e -> app.showScreen("DASHBOARD"));
        panel.add(backBtn);
        
        return panel;
    }
    
    private JPanel createRosterPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(new Color(30, 30, 40));
        
        String[] columns = {"Name", "Race", "STR", "AGI", "END", "INT", "WIS", "CHA", "PRE"};
        rosterModel = new DefaultTableModel(columns, 0) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return false;
            }
        };
        
        rosterTable = new JTable(rosterModel);
        rosterTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        rosterTable.getSelectionModel().addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                showFighterDetails();
            }
        });
        
        JScrollPane scrollPane = new JScrollPane(rosterTable);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        // Free Agents button
        JButton freeAgentsBtn = new JButton("View Free Agents");
        freeAgentsBtn.addActionListener(e -> showFreeAgents());
        panel.add(freeAgentsBtn, BorderLayout.SOUTH);
        
        return panel;
    }
    
    private JPanel createDetailsPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(new Color(30, 30, 40));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.gridx = 0;
        gbc.gridy = 0;
        
        // Fighter Details
        JLabel detailsTitle = new JLabel("Fighter Details");
        detailsTitle.setFont(new Font("Arial", Font.BOLD, 16));
        detailsTitle.setForeground(new Color(200, 50, 50));
        panel.add(detailsTitle, gbc);
        
        gbc.gridy++;
        fighterDetailsArea = new JTextArea(15, 30);
        fighterDetailsArea.setEditable(false);
        fighterDetailsArea.setFont(new Font("Monospace", Font.PLAIN, 12));
        fighterDetailsArea.setBackground(new Color(20, 20, 30));
        fighterDetailsArea.setForeground(Color.WHITE);
        JScrollPane detailsScroll = new JScrollPane(fighterDetailsArea);
        panel.add(detailsScroll, gbc);
        
        // Training section
        gbc.gridy++;
        JLabel trainLabel = new JLabel("Train Stat:");
        trainLabel.setForeground(Color.LIGHT_GRAY);
        panel.add(trainLabel, gbc);
        
        gbc.gridx = 1;
        statCombo = new JComboBox<>(new String[]{"STRENGTH", "AGILITY", "ENDURANCE", 
            "INTELLIGENCE", "WISDOM", "CHARISMA", "PRESENCE"});
        panel.add(statCombo, gbc);
        
        gbc.gridx = 0;
        gbc.gridy++;
        JButton trainBtn = new JButton("Train (100 gold)");
        trainBtn.addActionListener(e -> trainSelectedFighter());
        panel.add(trainBtn, gbc);
        
        // Equipment section
        gbc.gridx = 0;
        gbc.gridy++;
        gbc.gridwidth = 2;
        JButton equipBtn = new JButton("Manage Equipment");
        equipBtn.addActionListener(e -> manageEquipment());
        panel.add(equipBtn, gbc);
        
        // Release fighter
        gbc.gridy++;
        JButton releaseBtn = new JButton("Release Fighter");
        releaseBtn.setForeground(Color.RED);
        releaseBtn.addActionListener(e -> releaseSelectedFighter());
        panel.add(releaseBtn, gbc);
        
        return panel;
    }
    
    /**
     * Refresh the screen
     */
    public void refresh() {
        // Update team combo
        teamCombo.removeAllItems();
        for (Team team : gameStateManager.getTeams()) {
            teamCombo.addItem(team.getName());
        }
        
        refreshRoster();
    }
    
    private void refreshRoster() {
        rosterModel.setRowCount(0);
        String selectedTeam = (String) teamCombo.getSelectedItem();
        
        if (selectedTeam != null) {
            Team team = findTeamByName(selectedTeam);
            if (team != null) {
                for (Warrior warrior : team.getWarriors()) {
                    Object[] row = {
                        warrior.getFullName(),
                        warrior.getRace(),
                        warrior.getStat(Stat.STRENGTH),
                        warrior.getStat(Stat.AGILITY),
                        warrior.getStat(Stat.ENDURANCE),
                        warrior.getStat(Stat.INTELLIGENCE),
                        warrior.getStat(Stat.WISDOM),
                        warrior.getStat(Stat.CHARISMA),
                        warrior.getStat(Stat.PRESENCE)
                    };
                    rosterModel.addRow(row);
                }
            }
        }
    }
    
    private void showFighterDetails() {
        int selectedRow = rosterTable.getSelectedRow();
        if (selectedRow >= 0) {
            String name = (String) rosterModel.getValueAt(selectedRow, 0);
            Warrior warrior = findWarriorByName(name);
            
            if (warrior != null) {
                StringBuilder sb = new StringBuilder();
                sb.append("Name: ").append(warrior.getFullName()).append("\n");
                sb.append("Race: ").append(warrior.getRace()).append("\n");
                sb.append("Age: ").append(warrior.getAge()).append("\n");
                sb.append("\nStats:\n");
                sb.append("  STR: ").append(warrior.getStat(Stat.STRENGTH)).append("\n");
                sb.append("  AGI: ").append(warrior.getStat(Stat.AGILITY)).append("\n");
                sb.append("  END: ").append(warrior.getStat(Stat.ENDURANCE)).append("\n");
                sb.append("  INT: ").append(warrior.getStat(Stat.INTELLIGENCE)).append("\n");
                sb.append("  WIS: ").append(warrior.getStat(Stat.WISDOM)).append("\n");
                sb.append("  CHA: ").append(warrior.getStat(Stat.CHARISMA)).append("\n");
                sb.append("  PRE: ").append(warrior.getStat(Stat.PRESENCE)).append("\n");
                sb.append("\nEquipment:\n");
                
                Weapon mainWeapon = warrior.getMainHandWeapon();
                if (mainWeapon != null) {
                    sb.append("  Main Hand: ").append(mainWeapon.getName()).append("\n");
                }
                
                ArmorPiece armor = warrior.getBodyArmor();
                if (armor != null) {
                    sb.append("  Armor: ").append(armor.getType()).append("\n");
                }
                
                fighterDetailsArea.setText(sb.toString());
            }
        }
    }
    
    private void trainSelectedFighter() {
        int selectedRow = rosterTable.getSelectedRow();
        if (selectedRow >= 0) {
            String name = (String) rosterModel.getValueAt(selectedRow, 0);
            Warrior warrior = findWarriorByName(name);
            
            if (warrior != null) {
                try {
                    Stat stat = Stat.valueOf((String) statCombo.getSelectedItem());
                    gameStateManager.trainWarrior(warrior, stat);
                    JOptionPane.showMessageDialog(this, 
                        warrior.getFullName() + " trained in " + stat + "!",
                        "Training Complete", JOptionPane.INFORMATION_MESSAGE);
                    refreshRoster();
                    showFighterDetails();
                } catch (Exception e) {
                    JOptionPane.showMessageDialog(this, 
                        "Training failed: " + e.getMessage(),
                        "Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        } else {
            JOptionPane.showMessageDialog(this, 
                "Please select a fighter first",
                "No Selection", JOptionPane.WARNING_MESSAGE);
        }
    }
    
    private void manageEquipment() {
        int selectedRow = rosterTable.getSelectedRow();
        if (selectedRow >= 0) {
            String name = (String) rosterModel.getValueAt(selectedRow, 0);
            Warrior warrior = findWarriorByName(name);
            
            if (warrior != null) {
                JDialog dialog = createEquipmentDialog(warrior);
                dialog.setVisible(true);
            }
        } else {
            JOptionPane.showMessageDialog(this, 
                "Please select a fighter first",
                "No Selection", JOptionPane.WARNING_MESSAGE);
        }
    }
    
    private JDialog createEquipmentDialog(Warrior warrior) {
        JDialog dialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(this), 
            "Equipment - " + warrior.getFullName(), true);
        dialog.setLayout(new GridLayout(0, 1, 10, 10));
        dialog.setSize(400, 300);
        dialog.setLocationRelativeTo(this);
        
        // Main hand weapon selection
        dialog.add(new JLabel("Main Hand Weapon:"));
        JComboBox<Weapon> mainWeaponCombo = new JComboBox<>();
        for (Weapon weapon : WeaponsUtil.getAllWeapons()) {
            mainWeaponCombo.addItem(weapon);
        }
        if (warrior.getMainHandWeapon() != null) {
            mainWeaponCombo.setSelectedItem(warrior.getMainHandWeapon());
        }
        dialog.add(mainWeaponCombo);
        
        // Off hand weapon selection
        dialog.add(new JLabel("Off Hand Weapon:"));
        JComboBox<Weapon> offWeaponCombo = new JComboBox<>();
        for (Weapon weapon : WeaponsUtil.getAllWeapons()) {
            offWeaponCombo.addItem(weapon);
        }
        if (warrior.getOffHandWeapon() != null) {
            offWeaponCombo.setSelectedItem(warrior.getOffHandWeapon());
        }
        dialog.add(offWeaponCombo);
        
        // Body armor selection
        dialog.add(new JLabel("Body Armor:"));
        JComboBox<ArmorPiece> armorCombo = new JComboBox<>();
        for (ArmorType type : ArmorType.values()) {
            armorCombo.addItem(new ArmorPiece(type));
        }
        if (warrior.getBodyArmor() != null) {
            armorCombo.setSelectedItem(warrior.getBodyArmor());
        }
        dialog.add(armorCombo);
        
        // Buttons
        JPanel buttonPanel = new JPanel();
        JButton saveBtn = new JButton("Save");
        JButton cancelBtn = new JButton("Cancel");
        
        saveBtn.addActionListener(e -> {
            Weapon mainWeapon = (Weapon) mainWeaponCombo.getSelectedItem();
            Weapon offWeapon = (Weapon) offWeaponCombo.getSelectedItem();
            ArmorPiece armor = (ArmorPiece) armorCombo.getSelectedItem();
            
            warrior.equipWeapon(mainWeapon, Hand.MAIN);
            warrior.equipWeapon(offWeapon, Hand.OFF);
            warrior.equipArmor(armor);
            
            dialog.dispose();
            showFighterDetails();
        });
        
        cancelBtn.addActionListener(e -> dialog.dispose());
        
        buttonPanel.add(saveBtn);
        buttonPanel.add(cancelBtn);
        dialog.add(buttonPanel);
        
        return dialog;
    }
    
    private void releaseSelectedFighter() {
        int selectedRow = rosterTable.getSelectedRow();
        if (selectedRow >= 0) {
            String name = (String) rosterModel.getValueAt(selectedRow, 0);
            Warrior warrior = findWarriorByName(name);
            
            if (warrior != null) {
                int confirm = JOptionPane.showConfirmDialog(this,
                    "Are you sure you want to release " + warrior.getFullName() + "?",
                    "Confirm Release", JOptionPane.YES_NO_OPTION);
                
                if (confirm == JOptionPane.YES_OPTION) {
                    String teamName = (String) teamCombo.getSelectedItem();
                    Team team = findTeamByName(teamName);
                    
                    if (team != null) {
                        gameStateManager.releaseWarrior(team, warrior);
                        JOptionPane.showMessageDialog(this, 
                            warrior.getFullName() + " has been released.",
                            "Fighter Released", JOptionPane.INFORMATION_MESSAGE);
                        refreshRoster();
                    }
                }
            }
        } else {
            JOptionPane.showMessageDialog(this, 
                "Please select a fighter first",
                "No Selection", JOptionPane.WARNING_MESSAGE);
        }
    }
    
    private void showFreeAgents() {
        JDialog dialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(this), 
            "Free Agent Market", true);
        dialog.setLayout(new BorderLayout());
        dialog.setSize(800, 600);
        dialog.setLocationRelativeTo(this);
        
        String[] columns = {"Name", "Race", "STR", "AGI", "END", "INT", "Price"};
        DefaultTableModel model = new DefaultTableModel(columns, 0) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return false;
            }
        };
        
        for (Warrior warrior : gameStateManager.getFreeAgents()) {
            int price = 500 + (warrior.getTotalStats() * 50);
            Object[] row = {
                warrior.getFullName(),
                warrior.getRace(),
                warrior.getStat(Stat.STRENGTH),
                warrior.getStat(Stat.AGILITY),
                warrior.getStat(Stat.ENDURANCE),
                warrior.getStat(Stat.INTELLIGENCE),
                price
            };
            model.addRow(row);
        }
        
        JTable table = new JTable(model);
        JScrollPane scrollPane = new JScrollPane(table);
        dialog.add(scrollPane, BorderLayout.CENTER);
        
        // Hire button
        JPanel buttonPanel = new JPanel();
        JButton hireBtn = new JButton("Hire Selected");
        hireBtn.addActionListener(e -> {
            int selectedRow = table.getSelectedRow();
            if (selectedRow >= 0) {
                String name = (String) model.getValueAt(selectedRow, 0);
                Warrior warrior = findFreeAgentByName(name);
                String teamName = (String) teamCombo.getSelectedItem();
                Team team = findTeamByName(teamName);
                
                if (warrior != null && team != null) {
                    boolean success = gameStateManager.hireFreeAgent(team, warrior);
                    if (success) {
                        JOptionPane.showMessageDialog(dialog, 
                            "Hired " + warrior.getFullName() + "!",
                            "Success", JOptionPane.INFORMATION_MESSAGE);
                        dialog.dispose();
                        refreshRoster();
                    } else {
                        JOptionPane.showMessageDialog(dialog, 
                            "Failed to hire (insufficient funds?)",
                            "Error", JOptionPane.ERROR_MESSAGE);
                    }
                }
            }
        });
        
        JButton closeBtn = new JButton("Close");
        closeBtn.addActionListener(e -> dialog.dispose());
        
        buttonPanel.add(hireBtn);
        buttonPanel.add(closeBtn);
        dialog.add(buttonPanel, BorderLayout.SOUTH);
        
        dialog.setVisible(true);
    }
    
    private Team findTeamByName(String name) {
        for (Team team : gameStateManager.getTeams()) {
            if (team.getName().equals(name)) {
                return team;
            }
        }
        return null;
    }
    
    private Warrior findWarriorByName(String name) {
        String teamName = (String) teamCombo.getSelectedItem();
        Team team = findTeamByName(teamName);
        
        if (team != null) {
            for (Warrior warrior : team.getWarriors()) {
                if (warrior.getFullName().equals(name)) {
                    return warrior;
                }
            }
        }
        return null;
    }
    
    private Warrior findFreeAgentByName(String name) {
        for (Warrior warrior : gameStateManager.getFreeAgents()) {
            if (warrior.getFullName().equals(name)) {
                return warrior;
            }
        }
        return null;
    }
}
