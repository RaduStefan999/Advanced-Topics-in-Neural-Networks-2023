import torch
from tqdm import tqdm
from torch.utils.tensorboard import SummaryWriter
from torch.utils.data import DataLoader
from wba_manager import WBAManager


def accuracy(output, labels):
    fp_plus_fn = torch.logical_not(output == labels).sum().item()
    all_elements = len(output)
    return (all_elements - fp_plus_fn) / all_elements


def train(model, train_loader, criterion, optimizer, optimizer_name: str, device) -> tuple[float, float, list[float]]:
    model.train()

    all_outputs = []
    all_labels = []

    total_loss = 0
    batch_loses = []

    for data, labels in train_loader:
        data = data.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        def closure():
            closure_loss = criterion(model(data), labels)
            closure_loss.backward()
            return closure_loss

        output = model(data)
        loss = criterion(output, labels)
        total_loss += loss.item()
        batch_loses.append(loss.item())

        loss.backward()

        # torch.nn.utils.clip_grad_norm_(model.parameters(), 5)

        if optimizer_name == "SGD_SAM":
            optimizer.step(closure)
            optimizer.zero_grad()
        else:
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)

        output = output.softmax(dim=1).detach().cpu().squeeze()
        labels = labels.cpu().squeeze()
        all_outputs.append(output)
        all_labels.append(labels)

    all_outputs = torch.cat(all_outputs).argmax(dim=1)
    all_labels = torch.cat(all_labels)

    return round(accuracy(all_outputs, all_labels), 4), round(total_loss / len(train_loader), 4), batch_loses


def val(model, val_loader, criterion, device) -> tuple[float, float]:
    model.eval()

    all_outputs = []
    all_labels = []

    total_loss = 0

    for data, labels in val_loader:
        data = data.to(device, non_blocking=True)

        with torch.no_grad():
            output = model(data)

        output = output.softmax(dim=1).cpu().squeeze()

        loss = criterion(output, labels)
        total_loss += loss.item()

        labels = labels.squeeze()
        all_outputs.append(output)
        all_labels.append(labels)

    all_outputs = torch.cat(all_outputs).argmax(dim=1)
    all_labels = torch.cat(all_labels)

    return round(accuracy(all_outputs, all_labels), 4), round(total_loss / len(val_loader), 4)


def do_epoch(model, train_loader, val_loader, criterion, optimizer, optimizer_name: str, device) \
        -> tuple[float, float, list[float], float, float]:

    acc, epoch_loss, batch_loses = train(model, train_loader, criterion, optimizer, optimizer_name, device)
    acc_val, val_loss = val(model, val_loader, criterion, device)
    # torch.cuda.empty_cache()
    return acc, epoch_loss, batch_loses, acc_val, val_loss


def get_model_norm(model):
    norm = 0.0
    for param in model.parameters():
        norm += torch.norm(param)
    return norm


def train_epochs(wba_manager: WBAManager, epochs: int, model: torch.nn.Module, train_loader: DataLoader,
                 val_loader: DataLoader, criterion,
                 optimizer: torch.optim.Optimizer, optimizer_name: str, batch_size: int,  device: torch.device):

    writer = SummaryWriter()
    tbar = tqdm(tuple(range(epochs)))

    writer.add_text("Optimizer Name", optimizer_name)
    writer.add_scalar("Batch size", batch_size)

    wba_manager.log({
        "Optimizer Name": optimizer_name,
        "Batch size": batch_size
    })

    for epoch in tbar:
        acc, epoch_loss, batch_loses, acc_val, val_loss = do_epoch(model, train_loader, val_loader, criterion,
                                                                   optimizer, optimizer_name, device)
        tbar.set_postfix_str(f"Acc: {acc}, Acc_val: {acc_val}")
        writer.add_scalar("Train/Accuracy", acc, epoch)
        writer.add_scalar("Epoch Train/Loss", epoch_loss, epoch)
        writer.add_scalar("Val/Accuracy", acc_val, epoch)
        writer.add_scalar("Val/Loss", val_loss, epoch)
        writer.add_scalar("Model/Norm", get_model_norm(model), epoch)

        for it, individual_batch_loss in enumerate(batch_loses):
            writer.add_scalar("Batch Train/Loss", individual_batch_loss, epoch * epochs + it)

        wba_manager.log({
            "Train/Accuracy": acc,
            "Epoch Train/Loss": epoch_loss,
            "Val/Accuracy": acc_val,
            "Val/Loss": val_loss,
            "Model/Norm": get_model_norm(model),
        })

        for it, individual_batch_loss in enumerate(batch_loses):
            wba_manager.log({"Batch Train/Loss": individual_batch_loss})
