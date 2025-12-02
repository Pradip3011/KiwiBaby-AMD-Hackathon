import * as vscode from 'vscode';
import fetch from 'node-fetch';

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand('aiTest.generate', async () => {
    const editor = vscode.window.activeTextEditor;
    const selection = editor?.document.getText(editor.selection) || '';
    const requirement = selection || await vscode.window.showInputBox({ prompt: 'Paste requirement' });
    if(!requirement) return;

    const res = await fetch('http://localhost:8000/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requirement, output_format: 'json' })
    });
    const j = await res.json();
    const doc = await vscode.workspace.openTextDocument({ content: JSON.stringify(j, null, 2), language: 'json' });
    await vscode.window.showTextDocument(doc);
  });
  context.subscriptions.push(disposable);
}

export function deactivate() {}
